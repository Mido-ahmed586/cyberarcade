import subprocess
from pathlib import Path
import httpx
import base64


_here = Path(__file__).resolve()
PROJECT_ROOT = _here.parents[5] if len(_here.parents) > 5 else _here.parents[min(2, len(_here.parents) - 1)]
SCENARIOS_DIR = Path(__import__("os").environ.get("SCENARIOS_BASE") or (PROJECT_ROOT / "scenarios"))
META_SCENARIO_DIR = SCENARIOS_DIR / "metasploit-basics"

GUACAMOLE_BASE = "http://localhost:8080/guacamole"
GUACAMOLE_ADMIN_USER = "guacadmin"
GUACAMOLE_ADMIN_PASS = "guacadmin"
GUACAMOLE_DATASOURCE = "postgresql"

# meta_kali SSH is exposed on port 2221 of the host
META_KALI_SSH_HOST = "host.docker.internal"
META_KALI_SSH_PORT = "2221"
META_KALI_SSH_USER = "student"
META_KALI_SSH_PASS = "cyber123"
META_GUAC_CONNECTION_NAME = "Metasploit Basics Lab - Kali"


def run_command(command: list[str], cwd: Path = META_SCENARIO_DIR):
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


def start_meta_lab():
    try:
        if not META_SCENARIO_DIR.exists():
            return {"success": False, "error": f"Scenario path does not exist: {META_SCENARIO_DIR}"}
        subprocess.Popen(
            ["docker", "compose", "up", "-d", "--build"],
            cwd=str(META_SCENARIO_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {"success": True, "message": "Lab containers starting in background"}
    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error": str(e)}


def stop_meta_lab():
    return run_command(["docker", "compose", "down"])


def reset_meta_lab():
    down = stop_meta_lab()
    up = start_meta_lab()
    return {"success": up["success"], "down": down, "up": up}


def autosolve_meta_lab():
    return run_command([
        "docker", "exec", "cyber_kali_msf",
        "bash", "-lc",
        "tmux has-session -t cyberlab 2>/dev/null "
        "  || tmux new-session -d -s cyberlab; "
        "tmux send-keys -t cyberlab 'clear' Enter; "
        "tmux send-keys -t cyberlab "
        "  \"echo '=== CyberArcade Metasploit Autosolve ==='\" Enter; "
        "tmux send-keys -t cyberlab 'nmap -sV metasploitable2' Enter; "
        "tmux send-keys -t cyberlab \"echo '[+] Reconnaissance done — launch msfconsole to exploit'\" Enter",
    ])


def check_meta_lab():
    return run_command(["docker", "compose", "ps"])


# ─── Guacamole auto-login ─────────────────────────────────────────────────────

_META_CONNECTION_PAYLOAD = {
    "name": META_GUAC_CONNECTION_NAME,
    "protocol": "ssh",
    "parameters": {
        "hostname": META_KALI_SSH_HOST,
        "port": META_KALI_SSH_PORT,
        "username": META_KALI_SSH_USER,
        "password": META_KALI_SSH_PASS,
        "color-scheme": "white-black",
        "font-size": "14",
        "terminal-type": "xterm",
    },
    "attributes": {
        "max-connections": "10",
        "max-connections-per-user": "",
    },
}


def get_meta_terminal_url() -> dict:
    # From inside Docker, localhost doesn't reach host ports — use host.docker.internal
    _internal = GUACAMOLE_BASE.replace("http://localhost:", "http://host.docker.internal:")
    try:
        with httpx.Client(timeout=10) as client:
            token_resp = client.post(
                f"{_internal}/api/tokens",
                data={"username": GUACAMOLE_ADMIN_USER, "password": GUACAMOLE_ADMIN_PASS},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token_resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"Guacamole auth failed ({token_resp.status_code}): {token_resp.text}",
                }
            auth_token = token_resp.json()["authToken"]

            conn_id = _find_or_create_meta_connection(client, auth_token, _internal)
            if not conn_id:
                return {"success": False, "error": "Could not create Guacamole connection"}

            raw = f"{conn_id}\x00c\x00{GUACAMOLE_DATASOURCE}"
            encoded_id = base64.b64encode(raw.encode()).decode()
            url = (
                f"http://localhost:8080/guacamole"
                f"/#/client/{encoded_id}"
                f"?token={auth_token}"
            )
            return {"success": True, "url": url}

    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Guacamole is not reachable. Make sure Docker containers are running.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_meta_machines_info() -> dict:
    """Return live IP addresses of both lab containers for the machine info panel."""
    def _container_ip(name: str) -> str:
        try:
            r = subprocess.run(
                ["docker", "inspect", "--format",
                 "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", name],
                capture_output=True, text=True, timeout=5,
            )
            return r.stdout.strip() if r.returncode == 0 else "unknown"
        except Exception:
            return "unknown"

    return {
        "success": True,
        "attacker": {
            "label": "Kali Linux (Attacker)",
            "ip": _container_ip("cyber_kali_msf"),
            "user": META_KALI_SSH_USER,
            "password": META_KALI_SSH_PASS,
        },
        "target": {
            "label": "Metasploitable2 (Target)",
            "hostname": "metasploitable2",
            "ip": _container_ip("metasploitable2"),
        },
    }


def _find_or_create_meta_connection(client: httpx.Client, token: str, base: str) -> str | None:
    params = {"token": token}

    resp = client.get(
        f"{base}/api/session/data/{GUACAMOLE_DATASOURCE}/connections",
        params=params,
    )
    if resp.status_code == 200:
        for conn_id, conn in resp.json().items():
            if conn.get("name") == META_GUAC_CONNECTION_NAME:
                client.put(
                    f"{base}/api/session/data/{GUACAMOLE_DATASOURCE}/connections/{conn_id}",
                    params=params,
                    json=_META_CONNECTION_PAYLOAD,
                )
                return conn_id

    create_resp = client.post(
        f"{base}/api/session/data/{GUACAMOLE_DATASOURCE}/connections",
        params=params,
        json=_META_CONNECTION_PAYLOAD,
    )
    if create_resp.status_code in (200, 201):
        return create_resp.json().get("identifier")

    return None
