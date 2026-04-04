# Copyright (c) 2024, Moataz M Hassan (Arkan Lab)
# Developer Website: https://arkan.it.com
# License: MIT
# For license information, please see license.txt

"""
Arrowz Engine - Shell Command Utility

Provides a safe wrapper around subprocess.run for executing system
commands with proper timeout handling, logging, and error management.
"""

import logging
import shlex
import subprocess
from typing import Tuple

logger = logging.getLogger("arrowz_engine.utils.shell")


def run_command(
    cmd: str,
    timeout: int = 30,
    check: bool = False,
    shell: bool = True,
    cwd: str = None,
) -> Tuple[str, str, int]:
    """
    Execute a shell command safely and return its output.

    Args:
        cmd: The command string to execute.
        timeout: Maximum seconds to wait for the command to complete.
                 Defaults to 30 seconds.
        check: If True, raise CalledProcessError on non-zero exit code.
        shell: If True, execute via /bin/sh (required for pipes, redirects).
               If False, the cmd string is split with shlex.
        cwd: Working directory for the command. Defaults to None (current dir).

    Returns:
        Tuple of (stdout, stderr, returncode).
        stdout and stderr are decoded UTF-8 strings with trailing
        whitespace stripped.

    Raises:
        subprocess.TimeoutExpired: If the command exceeds the timeout.
        subprocess.CalledProcessError: If check=True and exit code != 0.
        OSError: If the command cannot be executed.

    Example:
        >>> stdout, stderr, rc = run_command("ip addr show", timeout=10)
        >>> if rc == 0:
        ...     print(stdout)
    """
    logger.debug("Executing: %s (timeout=%ds)", cmd, timeout)

    try:
        if shell:
            args = cmd
        else:
            args = shlex.split(cmd)

        result = subprocess.run(
            args,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        stdout = result.stdout.rstrip() if result.stdout else ""
        stderr = result.stderr.rstrip() if result.stderr else ""

        if result.returncode != 0:
            logger.debug(
                "Command returned %d: cmd=%s stderr=%s",
                result.returncode,
                cmd,
                stderr[:200],
            )

        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, stdout, stderr
            )

        return stdout, stderr, result.returncode

    except subprocess.TimeoutExpired:
        logger.error("Command timed out after %ds: %s", timeout, cmd)
        raise
    except OSError as exc:
        logger.error("Failed to execute command '%s': %s", cmd, exc)
        raise
