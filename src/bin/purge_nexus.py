#!/usr/bin/env python3

from pdb import set_trace
import argparse

from collections import namedtuple
from copy import deepcopy

from infra import STALE_DATE
from infra.gav import GAV
from infra.gav_tree import GAVtree
from infra.product import Product
from infra.config import get_my_servers
from infra.config import my_servers
from infra.utils import is_earlier_version

from infra.nexus import Nexus

args = None
nexus = None
products = []


def setup():
    global nexus, products, args
    get_my_servers()

    print("args: %s" % args)

    nexus = Nexus(my_servers['NEXUS'])

    products = [
        Product('gov-site', verbose=args.verbose),
        Product('mygov-site', verbose=args.verbose),
    ]


ProductReleases = namedtuple('ProductReleases', ['recent', 'stale'])
Artefacts = namedtuple('Artefacts', ['recent', 'stale'])


def _get_product_releases(products):
    recent = []
    stale = []
    for product in products:
        recent.extend(product.recent_releases())
        stale.extend(product.stale_releases())

    return ProductReleases(recent=recent, stale=stale)


def _print_product_releases(product_releases):
    print("\nRELEASES:")
    print("\nStale Releases: ")
    for x in product_releases.stale:
        print(x)
    print("\nRecent Releases: ")
    for x in product_releases.recent:
        print(x)


def _get_artefacts(product_releases):
    recent = GAVtree("recent")
    stale = GAVtree("stale")

    for pr in product_releases.recent:
        for gav in pr.gavs():
            recent.add(gav)

    for pr in product_releases.stale:
        for gav in pr.gavs():
            stale.add(gav)

    return Artefacts(recent=recent, stale=stale)


def _print_gotten_artefacts(artefacts):
    print("\nARTEFACTS: ")
    artefacts.recent.prettyprint()
    artefacts.stale.prettyprint()


def _known_artefacts(artefacts):
    # Create list of all versions for named artefacts in recent and stale
    # (Ideally we would list all artefacts in nexus, but this breaks 10k limit)
    known = GAVtree("known")
    done = set()
    for tree in [artefacts.recent, artefacts.stale]:
        for groupId in tree._tree:
            for artefactId in tree._tree[groupId]:
                if not args.verbose:
                    print('.', end='.', flush=True)
                key = (groupId, artefactId)
                if key in done:
                    continue
                for version in nexus.artefact_versions(groupId, artefactId):
                    gav = GAV(groupId, artefactId, version)
                    known.add(gav)
                done.add(key)
    return known


def must_keep_artefact(groupId, artefactId):
    Snapshot = namedtuple('Snapshot', ['group', 'artefact'])
    snapshots = [
        Snapshot(group='scot.mygov.amphora', artefact='amphora-client'),
        Snapshot(group='org.mygovscot.beta', artefact='authentication-api'),
        Snapshot(group='org.mygovscot.beta', artefact='authentication-client'),
        Snapshot(group='org.mygovscot.beta', artefact='authentication-spring'),
        Snapshot(group='org.mygovscot.publishing', artefact='publishing-api'),
    ]

    # Keep anything mentioned as a snapshot in jenkins:resources/mygov.yaml
    for snapshot in snapshots:
        if groupId == snapshot.group and artefactId == snapshot.artefact:
            if args.verbose:
                print("keeping all snapshot %s:%s" % (groupId, artefactId))
            return True
    return False


def _create_initial_purge_list(artefacts):
    """From recent and stale artefacts, determine the artefacts to be removed.

    Rules:
    1. Keep everything explicitly referenced by recent releases
    2. Keep all versions of the SNAPSHOTS
    3. Delete versions older than the oldest kept version;
        do not delete anything newer than the oldest kept version.
    """

    def _must_keep_version(groupId, artefactId, version):
        if not artefacts.recent.has_artefact(groupId, artefactId):
            # can delete all versions
            return False

        earliest_used = artefacts.recent.earliest_version(groupId, artefactId)
        must_keep = (not is_earlier_version(version, earliest_used))
        return must_keep

    def _add_to_purge_from_group(known, purge, groupId):
        if args.verbose:
            print("known: %s" % groupId)
        for artefactId in known.artefacts(groupId):
            _add_to_purge_from_artefact(known, purge, groupId, artefactId)

    def _add_to_purge_from_artefact(known, purge, groupId, artefactId):
        if args.verbose:
            print("known:art:%s" % artefactId)

        if must_keep_artefact(groupId, artefactId):
            return

        for version in known.versions(groupId, artefactId):
            if _must_keep_version(groupId, artefactId, version):
                continue

            purge.add(GAV(groupId, artefactId, version), verbose=False)

    known = _known_artefacts(artefacts)

    print("\n\tcreated list of known artefacts")
    if args.verbose:
        known.prettyprint()
        print()
        print("""
*** The above is ALL artefacts referenced by ALL releases.
***   ('All releases' = both current and stale)
""")
        input("continue ?")

    purge = GAVtree('purge')
    for groupId in known.groups():
        _add_to_purge_from_group(known, purge, groupId)

    print("\tcreated initial purge list")
    return purge


def has_related_artifacts(groupId, artifactId):
    """
    >>> has_related_artifacts('org.mygovscot.publishing', 'publishing-deb')
    True
    >>> has_related_artifacts('org.mygovscot.beta', 'authentication-deb')
    True
    >>> has_related_artifacts('org.mygovscot.beta', 'web-site')
    False
    """
    Beta = 'org.mygovscot.beta'
    if not (artifactId.endswith('-deb') or artifactId.endswith('-debian')):
        return False
    if groupId == Beta and artifactId != 'authentication-deb':
        return False
    return True


def _should_add_wildcard_artefact(groupId, artifactId):
    """
    >>> _should_add_wildcard_artefact('org.mygovscot.publishing', 'publishing-deb')
    True
    >>> _should_add_wildcard_artefact('org.mygovscot.publishing', 'publishing-service')
    True
    >>> _should_add_wildcard_artefact('org.mygovscot.beta', 'authentication-deb')
    True
    >>> _should_add_wildcard_artefact('org.mygovscot.beta', 'authentication-service')
    True
    >>> _should_add_wildcard_artefact('org.mygovscot.beta', 'web-site')
    False
    """

    Beta = 'org.mygovscot.beta'

    if groupId == Beta and artifactId.find('authentication') == -1:
        return False

    if must_keep_artefact(groupId, artifactId):
        return False

    return True


def _add_wildcards_to_purge_list(purge):
    """
    From this list of artefacts, look for any which should be treated
    as wildcards, and add the related artefacts to purge list.

    RULES:
    1. For Java groups ("-deb"), also delete related artefacts w/ same version
    2. Delete all artefacts in the Beta group w/ same version
         which have 'authentication' in their artefactId
    """

    purge2 = deepcopy(purge)
    for groupId in purge.groups():
        for artifactId in purge.artefacts(groupId):
            if not has_related_artifacts(groupId, artifactId):
                continue
            """
            delete wildcards w/ same groupId/version
            if '-deb', wildcards are all other artefacts with same versions
            if Beta, wildcards are as above with extra limitation that
                artefactId must match '*authentication*'
            """
            for version in purge.versions(groupId, artifactId):
                if args.verbose:
                    print("get wildcards: %s:%s:%s" % (groupId, artifactId,
                                                       version))
                for art in nexus.related_artefactIds(groupId, version):
                    if _should_add_wildcard_artefact(groupId, art):
                        purge2.add(GAV(groupId, art, version), verbose=False)
    return purge2


def _do_purge(final):
    for gav in final.gavs():
        nexus.delete_gav_and_its_assets(gav)


def prune_nexus():
    print("""
Pruning stale build artefacts in Nexus
  ('stale'='unused in release since %s')
""" % STALE_DATE)

    print("""
*** #1: Collect Product Releases, both recent and stale
""")
    product_releases = _get_product_releases(products)

    if args.verbose:
        print()
        print("*** Product releases collected, recent and stale")
        input("continue? (next step: get artefact lists)")
        print()

    print("""
*** #2: Analyse recent and stale product releases.
        Make 2 lists of artefacts used:
        a) by recent product releases
        b) by stale product releases

        Note: there may be overlap between these two lists.
""")
    artefacts = _get_artefacts(product_releases)

    if args.verbose:
        _print_gotten_artefacts(artefacts)
        print()
        print("*** Artefact lists collected")
        input("continue? (next step: determine initial purge list)")
        print()

    print("""
*** #3: Create initial purge list.
""")
    initial_purge = _create_initial_purge_list(artefacts)

    if initial_purge.is_empty():
        print("Nothing to purge")
        return

    if args.verbose:
        initial_purge.prettyprint()
        print()
        print("*** Artefacts analysed")
        input("continue? (next step: add in wildcards)")
        print()

    print("""
*** #4: Add wildcards to purge list.
""")
    final_purge = _add_wildcards_to_purge_list(initial_purge)

    if args.verbose or args.dryrun:
        print("""
FINAL PURGE LIST:
""")
        final_purge.prettyprint()

    if args.dryrun:
        #         yn = input("""
        # These are the artefacts in the final purge list; purge them? (y/n) """)
        #         if yn != 'y':
        print("DRYRUN: stopping before performing purge")
        return

    if args.verbose:
        print()
        input("continue? (next step: do the purge)")

    print("""
    *** #5: Perform purge.
    """)
    _do_purge(final_purge)

    print("""
    *** #6: Compact blobstore.
    """)

    nexus.compact_blobstore()

    print("""
    *** #7: Done.
    """)


def get_args():
    global args
    parser = argparse.ArgumentParser(
        description='Prune stale artefacts from Nexus')
    parser.add_argument(
        '-r', '--dryrun', dest='dryrun', action='store_true', default=False)
    parser.add_argument(
        '-d', '--debug', dest='debug', action='store_true', default=False)
    parser.add_argument(
        '-v', '--verbose', dest='verbose', action='store_true', default=False)
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    get_args()
    setup()
    if args.debug:
        set_trace()
    prune_nexus()

# eof
