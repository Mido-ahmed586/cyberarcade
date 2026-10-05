"""
Guacamole AutoSolve execution engine for CyberArcade.

Architecture
------------
For each autosolve command we do TWO things in parallel:

  1. tmux send-keys → command appears visibly in the Guacamole terminal
     (the student watches it type and run in real-time)

  2. docker exec bash -c → clean stdout capture
     (used to stream output lines to the frontend log and extract the answer)

The tmux session name "lab" matches the auto-attach rule in .bashrc:
    exec tmux new-session -A -s lab
which runs every time the student's SSH session opens (i.e. when Guacamole connects).

Answer extraction
-----------------
If the clean output (stripped, whitespace-normalised) equals the stored
expected_answer → we use the real output (authentic answer from the VM).
Otherwise we fall back to expected_answer from the DB so the answer field
is always filled correctly even for verbose/demonstration commands.
"""
from __future__ import annotations

import asyncio
import re
import subprocess

# ── Container routing ──────────────────────────────────────────────────────────
CONTAINER_MAP: dict[str, str] = {
    "df-kali":        "cyber_df_kali",
    "ssh-bruteforce": "cyber_attacker_kali",
    "metasploit":     "cyber_kali_msf",
}

TMUX_SESSION = "lab"   # matches setup_evidence.sh / student .bashrc
EXEC_TIMEOUT = 30      # seconds per docker exec command


# ── Low-level subprocess helpers ───────────────────────────────────────────────

def _run(args: list[str], timeout: int = 10) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(
            args, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"
    except Exception as exc:
        return 1, "", str(exc)


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*[mGKHFJ]", "", text)


# ── Container / session management ─────────────────────────────────────────────

def container_is_running(name: str) -> bool:
    rc, out, _ = _run(
        ["docker", "inspect", "--format", "{{.State.Running}}", name],
        timeout=6,
    )
    return rc == 0 and out.strip().lower() == "true"


def ensure_tmux_session(container: str, session: str = TMUX_SESSION) -> bool:
    """
    Check if the tmux session exists inside the container (as student user).
    Creates a detached session if missing so tmux_send always has a target.
    When the student opens Guacamole the SSH login triggers .bashrc which
    attaches to this same session, making the commands visible.
    """
    rc, _, _ = _run(
        ["docker", "exec", "--user", "student", container,
         "tmux", "has-session", "-t", session],
        timeout=5,
    )
    if rc != 0:
        rc2, _, _ = _run(
            [
                "docker", "exec", "--user", "student", container,
                "tmux", "new-session", "-d", "-s", session,
                "-x", "220", "-y", "50",
            ],
            timeout=8,
        )
        return rc2 == 0
    return True


# ── Command injection and capture ──────────────────────────────────────────────

def scroll_terminal(container: str, direction: str = "up", lines: int = 5, session: str = TMUX_SESSION) -> None:
    """Enter tmux copy-mode and scroll up/down, or exit copy-mode."""
    ensure_tmux_session(container, session)
    if direction == "exit":
        _run(["docker", "exec", "--user", "student", container,
              "tmux", "send-keys", "-t", f"{session}:0", "-X", "cancel"], timeout=5)
        return
    _run(["docker", "exec", "--user", "student", container,
          "tmux", "copy-mode", "-t", session], timeout=5)
    scroll_cmd = "scroll-up" if direction == "up" else "scroll-down"
    for _ in range(lines):
        _run(["docker", "exec", "--user", "student", container,
              "tmux", "send-keys", "-t", f"{session}:0", "-X", scroll_cmd], timeout=5)


def tmux_send(container: str, command: str, session: str = TMUX_SESSION) -> bool:
    """
    Inject *command* into the visible Guacamole tmux terminal via send-keys.
    Runs as student user so it reaches the correct tmux server socket.
    """
    rc, _, _ = _run(
        [
            "docker", "exec", "--user", "student", container,
            "tmux", "send-keys", "-t", f"{session}:0",
            command, "Enter",
        ],
        timeout=6,
    )
    return rc == 0


def exec_capture(
    container: str, command: str, timeout: int = EXEC_TIMEOUT
) -> tuple[str, int]:
    """
    Execute *command* inside the container as the student user via bash -c.
    Returns (stripped_stdout, return_code).
    ANSI escape codes are removed so the output is clean text.
    """
    rc, out, _ = _run(
        ["docker", "exec", "--user", "student", container, "bash", "-c", command],
        timeout=timeout,
    )
    return _strip_ansi(out).strip(), rc


# ── Task-level execution ───────────────────────────────────────────────────────

async def run_task_commands(
    container: str,
    commands: list[str],
    task_id: str,
    websocket,
) -> str:
    """
    Run every command in *commands* for a single task:
      - Inject into tmux (visible in Guacamole)
      - Execute via docker exec (clean output capture)
      - Stream each output line to the frontend via WebSocket

    Returns the clean stdout of the last command (answer candidate).
    """
    loop = asyncio.get_event_loop()
    last_output = ""

    for cmd in commands:
        # ── Announce command in the frontend log ──────────────────────────────
        await websocket.send_json({
            "type":    "output",
            "task_id": task_id,
            "data":    f"$ {cmd}",
        })

        # ── Visual injection into Guacamole terminal ──────────────────────────
        await loop.run_in_executor(None, tmux_send, container, cmd)

        # ── Clean execution for output capture ────────────────────────────────
        clean_out, _rc = await loop.run_in_executor(
            None, exec_capture, container, cmd
        )
        last_output = clean_out

        # ── Stream output lines to frontend ───────────────────────────────────
        for line in clean_out.splitlines():
            if line.strip():
                await websocket.send_json({
                    "type":    "output",
                    "task_id": task_id,
                    "data":    line,
                })

        # Brief pause so the terminal renders between commands
        await asyncio.sleep(0.7)

    return last_output


# ── Answer extraction ──────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    """Normalise for comparison: strip, collapse whitespace, lowercase."""
    return re.sub(r"\s+", " ", s.strip().lower())


def extract_answer(real_output: str, expected_answer: str) -> str:
    """
    Return *real_output* if it normalises to the same value as *expected_answer*.
    Also accepts if the expected answer appears as an exact line in the output.
    Falls back to *expected_answer* from the DB when there's no match — this
    correctly handles conceptual tasks (where command output is a demonstration,
    not the answer) and verbose commands whose output includes extra context.
    """
    if not real_output:
        return expected_answer

    # Full match
    if _norm(real_output) == _norm(expected_answer):
        return real_output.strip()

    # Line-level match: expected_answer appears as one of the output lines
    for line in real_output.splitlines():
        if _norm(line) == _norm(expected_answer):
            return line.strip()

    # No match → fall back to DB value (always correct)
    return expected_answer
