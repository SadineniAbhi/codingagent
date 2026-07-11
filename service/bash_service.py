import os
import subprocess
from utils.custom_errors import CommandFailed
from utils.logger import get_logger

logger = get_logger(__name__)

def run_command(command: str) -> subprocess.CompletedProcess[str]:
    try:
        logger.info("Running command")
        os.makedirs("/tmp/workspace", exist_ok=True)
        result = subprocess.run(
            command, shell=True, text=True, capture_output=True,
            cwd="/tmp/workspace",
        )
        logger.info("Command exited with code %s", result.returncode)
        return result
    except Exception as e:
        raise CommandFailed("Failed to run command", 500) from e
