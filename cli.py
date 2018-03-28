# -*- coding: utf-8 -*-
"""Console script for repo_clean."""
import sys
import click
from pdb import set_trace

from infra.repo import Repo

args = None


@click.option(
    '--dry-run',
    default=False,
    help="Do all the data gathering analysis, stop before taking action.",
    is_flag=True,
)
@click.option(
    '--debug',
    default=False,
    help="Stop for debugging.",
    is_flag=True,
)
@click.command()
def main(dry_run, debug):
    """Console script for repo_clean."""
    print("args: dry_run: %s, debug: %s" % (dry_run, debug))
    if debug:
        set_trace()

    repo = Repo()
    if not repo.nexus.host:
        print("Invalid config")
        exit(-1)

    purge_list = repo.purge_list()
    if dry_run or purge_list is None:
        return

    repo.do_purge(purge_list)
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

# eof
