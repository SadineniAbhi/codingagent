import os
import subprocess
from custom_errors import CommandFailed

def run_command(command: str) -> subprocess.CompletedProcess[str]:
    try:
        os.makedirs("/tmp/workspace", exist_ok=True)
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True,
            cwd="/tmp/workspace",
        )
        return result
    except Exception:
        raise CommandFailed("Failed to run command", 500)
