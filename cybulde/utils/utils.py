import logging
import socket
import subprocess


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"[{socket.gethostname()}] {name}")


# A simple utility to run shell commands


def run_shell_command(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # Run the command
    if result.returncode != 0 and result.stderr:  # Log a warning if the command fails
        logger = get_logger(__name__)
        logger.warning(f"Command '{cmd}' returned non-zero exit code {result.returncode}: {result.stderr}")
    return result.stdout
