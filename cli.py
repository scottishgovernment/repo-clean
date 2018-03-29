# -*- coding: utf-8 -*-
"""Console script for repo_clean."""
import sys
import os
import configparser
import click
from pdb import set_trace

from infra.repo import Repo

args = None


@click.option(
    '--config-file',
    type=click.Path(),
    default="~/repo-clean.ini",
)
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
def main(config_file, dry_run, debug):
    """Console script for repo_clean."""
    print("args: config_file: %s, dry_run: %s, debug: %s\n" % (config_file,
                                                               dry_run, debug))
    if debug:
        set_trace()

    filename = os.path.expanduser(config_file)

    if not os.path.exists(filename):
        print("Config file %s does not exist" % filename)
        exit(-1)

    config = configparser.ConfigParser()
    config.read(filename)
    params = {}
    for x in ['jenkins_host', 'nexus_host', 'nexus_user', 'nexus_password']:
        params[x] = config['DEFAULT'][x]
    for x in ['product_names']:
        val = config['DEFAULT'][x]
        params[x] = [thing.strip() for thing in val.split(',')]
    repo = Repo(**params)
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
