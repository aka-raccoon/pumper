from os import environ
from pathlib import Path
from sys import exit  # pylint: disable=redefined-builtin
from typing import Optional

from github import Github
from typer import Argument, Option, Typer

from pumper.logging import logger
from pumper.tools import GH_URL, Cz, Git

app = Typer(
    name="pumper",
    help="< Bump Push Merge >",
    pretty_exceptions_show_locals=False,
)


@app.command()
def create(  # pylint: disable=too-many-arguments,too-many-locals
    repo: str = Option(
        ..., envvar="GITHUB_REPOSITORY", help="The owner and repository name, eg 'owner/repo'."
    ),
    url: str = Option(GH_URL, envvar="GITHUB_API_URL", help="Github API url."),
    token: str = Option(..., envvar="GITHUB_TOKEN", help="Github token."),
    base: str = Option("main", envvar="BASE_BRANCH", help="Base branch of a PR."),
    branch: str = Option("release/{version}", help="Branch name and PR title."),
    user: str = Option("github-actions[bot]", help="Git user name."),
    email: str = Option("github-actions[bot]@users.noreply.github.com", help="Git user email."),
    gh_env: bool = Option(False, "--gh-env", help="Create 'PR_NUM' env var for GH actions"),
    label: Optional[list[str]] = Option(None, help="Add labels to PR."),
    assign: bool = Option(True, "--assign", help="Assign PR"),
    assignee: str = Option("", envvar="GITHUB_ACTOR", help="PR assignee name."),
):
    """Bump version, push branch and create pull request."""
    git = Git(repo=repo, user=user, email=email)
    if not git.is_initialized():
        logger.error("Not a git repository!")
        exit(1)

    git.setup()
    git.remove_local_tags()
    git.fetch_remote_tags()

    cz = Cz()

    version = cz.get_version()
    changelog, error, rc = cz.bump()

    no_increment = rc == 21
    if no_increment:
        logger.error(error)
        exit(1)
    new_version = cz.get_version()
    if version == new_version:
        logger.warning("No bump!")
        exit(0)

    branch = branch.format(version=version)
    git.create_branch(name=branch)

    gh = Github(base_url=url, login_or_token=token)
    logger.info("creating PR")
    pr = gh.get_repo(full_name_or_id=repo).create_pull(
        title=branch, body=changelog, head=branch, base=base
    )
    logger.info("PR %i created", pr.number)
    if label:
        logger.info("adding label(s) to PR")
        pr.add_to_labels(*label)
    if assign:
        logger.info("assigning PR to %s", assignee)
        pr.add_to_assignees(assignee)
    git.remove_local_tags()
    if gh_env:
        env_file = Path(environ["GITHUB_ENV"])
        logger.info("saving PR number to file %s", env_file)
        with env_file.open("a", encoding="utf-8") as file:
            file.write(f"PR_NUM={pr.number}")


@app.command()
def approve(
    pr_num: int = Argument(..., envvar="PR_NUM", help="PR number."),
    repo: str = Option(
        ..., envvar="GITHUB_REPOSITORY", help="The owner and repository name, eg 'owner/repo'."
    ),
    url: str = Option(GH_URL, envvar="GITHUB_API_URL", help="Github API url."),
    token: str = Option(..., envvar="GITHUB_TOKEN", help="Github token."),
    body: str = Option("🤖 Approved by GH actions!", help="PR message."),
):
    """Approve pull request."""
    gh = Github(base_url=url, login_or_token=token)
    pr = gh.get_repo(repo).get_pull(pr_num)
    logger.info("approving PR %i", pr_num)
    pr.create_review(body=body, event="APPROVE")


@app.command()
def merge(
    pr_num: int = Argument(..., envvar="PR_NUM", help="PR number."),
    repo: str = Option(
        ..., envvar="GITHUB_REPOSITORY", help="The owner and repository name, eg 'owner/repo'."
    ),
    url: str = Option(GH_URL, envvar="GITHUB_API_URL", help="Github API url."),
    token: str = Option(..., envvar="GITHUB_TOKEN", help="Github token."),
):
    """Merge pull request."""
    logger.info("merging PR %i", pr_num)
    pr = Github(base_url=url, login_or_token=token).get_repo(repo).get_pull(pr_num)
    pr.merge()


if __name__ == "__main__":
    app()
