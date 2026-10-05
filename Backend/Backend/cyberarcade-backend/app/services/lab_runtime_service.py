import subprocess
from pathlib import Path
import httpx
import base64


_here = Path(__file__).resolve()
PROJECT_ROOT = _here.parents[5] if len(_here.parents) > 5 else _here.parents[min(2, len(_here.parents) - 1)]
SCENARIOS_DIR = Path(__import__("os").environ.get("SCENARIOS_BASE") or (PROJECT_ROOT / "scenarios"))
TERMINAL_SCENARIO_DIR = SCENARIOS_DIR / "kali-terminal"
DF_KALI_SCENARIO_DIR = SCENARIOS_DIR / "df-kali"

# ── Guacamole bases for each runtime stack ─────────────────────────────────────
GUACAMOLE_BASE = "http://localhost:8081/guacamole"
DF_KALI_GUACAMOLE_BASE = "http://localhost:8082/guacamole"
GUAC_USERNAME = "student"
GUAC_PASSWORD = "student123"

# Connection IDs use Guacamole's format: base64("{name}\x00c\x00{datasource}")
# user-mapping.xml datasource is always "default"
ATTACKER_CONN_ID = base64.b64encode(
    b"Attacker Kali Terminal\x00c\x00default"
).decode().rstrip("=")

DEFENDER_CONN_ID = base64.b64encode(
    b"Defender Target Terminal\x00c\x00default"
).decode().rstrip("=")


def _get_guac_token(base: str) -> str | None:
    """POST to Guacamole /api/tokens and return the session token."""
    # From inside the Docker container, localhost doesn't reach host-mapped ports;
    # translate to host.docker.internal so the request reaches the right Guacamole.
    internal = base.replace("http://localhost:", "http://host.docker.internal:")
    try:
        with httpx.Client(timeout=8) as client:
            resp = client.post(
                f"{internal}/api/tokens",
                data={"username": GUAC_USERNAME, "password": GUAC_PASSWORD},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if resp.status_code == 200:
                return resp.json().get("authToken")
    except Exception:
        pass
    return None


def _guac_url(conn_id: str, token: str | None, base: str) -> str:
    url = f"{base}/#/client/{conn_id}"
    if token:
        url += f"?token={token}"
    return url


def _runtime_directory(slug: str = "ssh-bruteforce") -> Path:
    if slug == "df-kali":
        return DF_KALI_SCENARIO_DIR
    return TERMINAL_SCENARIO_DIR


def _guacamole_base(slug: str = "ssh-bruteforce") -> str:
    if slug == "df-kali":
        return DF_KALI_GUACAMOLE_BASE
    return GUACAMOLE_BASE


# ── Docker helpers ─────────────────────────────────────────────────────────────

def run_command(command: list[str], cwd: Path = TERMINAL_SCENARIO_DIR):
    try:
        if not cwd.exists():
            return {
                "success": False,
                "error": f"Scenario path does not exist: {cwd}",
                "command": " ".join(command),
            }
        result = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            shell=False,
        )
        return {
            "success": result.returncode == 0,
            "cwd": str(cwd),
            "command": " ".join(command),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except Exception as e:
        return {
            "success": False,
            "cwd": str(cwd),
            "command": " ".join(command),
            "error_type": type(e).__name__,
            "error": str(e),
        }


def _start_background(cwd: Path) -> dict:
    """Fire-and-forget docker compose up — returns immediately so HTTP doesn't time out during build."""
    try:
        if not cwd.exists():
            return {"success": False, "error": f"Scenario path does not exist: {cwd}"}
        subprocess.Popen(
            ["docker", "compose", "up", "-d", "--build"],
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"success": True, "message": "Lab containers starting in background"}
    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error": str(e)}


def start_ssh_lab():
    return _start_background(_runtime_directory("ssh-bruteforce"))


def stop_ssh_lab():
    return run_command(["docker", "compose", "down"], cwd=_runtime_directory("ssh-bruteforce"))


def reset_ssh_lab():
    down = stop_ssh_lab()
    up = start_ssh_lab()
    return {"success": up["success"], "down": down, "up": up}


def run_in_container(command: list[str], container_name: str):
    return run_command([
        "docker", "exec", "-u", "student",
        container_name, "bash", "-lc", command,
    ])


def run_in_kali(command: str):
    return run_in_container(command, "cyber_attacker_kali")


def run_in_df_kali(command: str):
    return run_in_container(command, "cyber_df_kali")


def run_in_target(command: str):
    return run_command([
        "docker", "exec",
        "cyber_defender_target", "bash", "-c", command,
    ])


def autosolve_ssh_lab():
    """Send guided autosolve commands into the attacker Kali tmux session."""
    return run_in_kali(
        "tmux has-session -t cyberlab 2>/dev/null "
        "  || tmux new-session -d -s cyberlab; "
        "tmux send-keys -t cyberlab 'clear' Enter; "
        "tmux send-keys -t cyberlab "
        "  \"echo '=== CyberArcade Guided Autosolve ==='\" Enter; "
        "tmux send-keys -t cyberlab 'whoami' Enter; "
        "tmux send-keys -t cyberlab 'hostname' Enter; "
        "tmux send-keys -t cyberlab 'ping -c 2 172.30.0.10' Enter; "
        "tmux send-keys -t cyberlab 'sudo nmap -sV 172.30.0.10' Enter; "
        "tmux send-keys -t cyberlab \"echo '[+] Guided Autosolve Complete'\" Enter"
    )


def check_ssh_lab():
    return run_command(["docker", "compose", "ps"])


# ── Terminal URLs ──────────────────────────────────────────────────────────────

def get_guacamole_terminal_url(slug: str = "ssh-bruteforce") -> dict:
    """Authenticated Guacamole URL for the Attacker Kali terminal."""
    try:
        base = _guacamole_base(slug)
        token = _get_guac_token(base)
        if not token:
            return {
                "success": False,
                "error": (
                    "Could not authenticate with Guacamole. "
                    "Make sure the runtime containers are running."
                ),
            }
        return {"success": True, "url": _guac_url(ATTACKER_CONN_ID, token, base)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_guacamole_defender_url(slug: str = "ssh-bruteforce") -> dict:
    """Authenticated Guacamole URL for the Defender Target terminal."""
    try:
        base = _guacamole_base(slug)
        token = _get_guac_token(base)
        if not token:
            return {
                "success": False,
                "error": (
                    "Could not authenticate with Guacamole. "
                    "Make sure the runtime containers are running."
                ),
            }
        return {"success": True, "url": _guac_url(DEFENDER_CONN_ID, token, base)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── df-kali (Digital Forensics) ────────────────────────────────────────────────
# Forensics labs are hosted in a dedicated df-kali runtime stack.
# The stack uses a separate Guacamole port and its own runtime compose path.

def start_df_kali_lab():
    return _start_background(_runtime_directory("df-kali"))


def stop_df_kali_lab():
    return run_command(["docker", "compose", "down"], cwd=_runtime_directory("df-kali"))


def reset_df_kali_lab():
    down = stop_df_kali_lab()
    up = start_df_kali_lab()
    return {"success": up["success"], "down": down, "up": up}


def autosolve_df_kali_lab():
    """Send guided autosolve commands into the df-kali Kali tmux session."""
    return run_in_df_kali(
        "tmux has-session -t cyberlab 2>/dev/null "
        "  || tmux new-session -d -s cyberlab; "
        "tmux send-keys -t cyberlab 'clear' Enter; "
        "tmux send-keys -t cyberlab "
        "  \"echo '=== Digital Forensics Guided Autosolve ==='\" Enter; "
        "tmux send-keys -t cyberlab 'ls -la' Enter; "
        "tmux send-keys -t cyberlab 'file *' Enter; "
        "tmux send-keys -t cyberlab 'stat *' Enter; "
        "tmux send-keys -t cyberlab "
        "  \"echo '[+] Guided Autosolve Complete'\" Enter"
    )


def check_df_kali_lab():
    return run_command(["docker", "compose", "ps"], cwd=_runtime_directory("df-kali"))


def get_df_kali_terminal_url() -> dict:
    """Authenticated Guacamole URL for the Forensics Kali terminal."""
    return get_guacamole_terminal_url("df-kali")
