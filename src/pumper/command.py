import sys
from shlex import split
from subprocess import CalledProcessError, run  # nosec
from typing import NamedTuple, Optional

from pumper.logging import logger


class Command(NamedTuple):
    stdout: str
    stderr: str
    rc: int


def execute(cmd: str, ignore: Optional[list] = None):
    output = run(split(cmd), text=True, encoding="utf-8", check=False, capture_output=True)  # nosec
    result = Command(output.stdout.strip(), output.stderr.strip(), output.returncode)
    should_not_raise = [(ignore and result.rc in ignore), (not result.rc)]
    if any(should_not_raise):
        return result
    logger.error(
        "Command execution has failed!\n%s",
        result.stderr,
        exc_info=CalledProcessError(
            stderr=result.stderr, output=result.stdout, returncode=result.rc, cmd=cmd
        ),
    )
    sys.exit(result.rc)
