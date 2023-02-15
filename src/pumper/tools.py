import re
import sys
from typing import Optional

from pumper.command import Command, execute
from pumper.logging import logger

GH_URL = "https://api.github.com"


class Tool:  # pylint: disable = too-few-public-methods
    def __init__(self, exe: str) -> None:
        self.exe = exe

    def _execute(self, args: str, ignore: Optional[list] = None) -> Command:
        return execute(cmd=f"{self.exe} {args}", ignore=ignore)


class Git(Tool):
    def __init__(self, repo: str, user: str, email: str, exe: str = "git"):
        super().__init__(exe=exe)
        self.repo = repo
        self.user = user
        self.email = email

    def is_initialized(self):
        not_git = 128
        *_, rc = self._execute(args="status", ignore=[not_git])
        return rc != not_git

    def setup(self):
        logger.info("configuring GIT")
        self._execute(args="config --local pull.rebase true")
        self._execute(args=f"config --local user.name {self.user}")
        self._execute(args=f"config --local user.email {self.email}")

    def remove_local_tags(self):
        logger.info("removing local tags")
        for tag in self._execute("tag -l").stdout.splitlines():
            self._execute(f"tag -d {tag}")

    def fetch_remote_tags(self):
        logger.info("fetching remote tags")
        self._execute("fetch --tags")

    def create_branch(self, name: str):
        logger.info("creating branch %s", name)
        self._execute(f"switch --create {name}")
        self._execute("push origin HEAD")


class Cz(Tool):
    def __init__(self, exe=f"{sys.executable} -m commitizen"):
        super().__init__(exe=exe)

    def get_version(self) -> str:
        logger.info("getting version")
        return self._execute("version --project").stdout

    def bump(self) -> tuple[str, str, int]:
        logger.info("bumping version")
        changelog, error, rc = self._execute(
            "bump --yes --changelog --changelog-to-stdout", ignore=[21]
        )
        return format_changelog(text=changelog), error, rc


def format_changelog(text: str) -> str:
    git_output = r".*\n \d+ files changed, \d+ insertions\(\+\), \d+ deletions\(\-\)"
    return re.sub(git_output, "", text)
