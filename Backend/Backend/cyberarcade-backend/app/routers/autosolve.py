import asyncio
import paramiko
from fastapi import APIRouter, WebSocket

router = APIRouter(prefix="/api/autosolve", tags=["autosolve"])

COMMANDS = [
    "clear",
    "echo '=== CyberArcade Autosolve Started ==='",
    "whoami",
    "hostname",
    "ping -c 3 172.30.0.10",
    "sudo nmap 172.30.0.10",
    "echo 'Autosolve Complete'"
]


@router.websocket("/ws")
async def autosolve_ws(websocket: WebSocket):
    await websocket.accept()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        await websocket.send_text("[+] Sending commands to Kali terminal...\n")

        ssh.connect(
            hostname="127.0.0.1",
            port=2223,
            username="student",
            password="student123",
            look_for_keys=False,
            allow_agent=False,
        )

        for cmd in COMMANDS:
            safe_cmd = cmd.replace("'", "'\"'\"'")
            ssh.exec_command(f"tmux send-keys -t cyberlab '{safe_cmd}' Enter")
            await websocket.send_text(f"[sent] {cmd}\n")
            await asyncio.sleep(2)

        await websocket.send_text("[+] Autosolve sent to Kali terminal.\n")

    except Exception as e:
        await websocket.send_text(f"[ERROR] {str(e)}\n")

    finally:
        ssh.close()
        await websocket.close()