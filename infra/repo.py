from pdb import set_trace
import collections
from copy import deepcopy

from .config import STALE_DATE, my_servers
from .gav import GAV
from .gav_tree import GAVtree
from .nexus import Nexus
from .product import Product
from .utils import is_earlier_version

ProductReleases = collections.namedtuple('ProductReleases',
                                         ['recent', 'stale'])
Artefacts = collections.namedtuple('Artefacts', ['recent', 'stale'])


class Repo():
    def __init__(self):
        self.nexus = Nexus(my_servers['NEXUS'])
        self.products = [
            Product('gov-site'),
            Product('mygov-site'),
        ]
        self.stale_date = STALE_DATE

    def purge_list(self):
        print(
            "Pruning stale build artefacts in Nexus (unused in release since %s)"
            % self.stale_date)

        print("*** #1: Collect Product Releases, both recent and stale")
        product_releases = self._get_product_releases()

        print("*** #2: Analyse recent and stale product releases.")
        # Make 2 lists of artefacts used:
        # a) by recent product releases
        # b) by stale product releases
        # Note: there may be overlap between these two lists.
        artefacts = _get_artefacts(product_releases)
        assert artefacts.recent

        print("*** #3: Create initial purge list.")
        initial_purge = self._create_initial_purge_list(artefacts)

        if initial_purge.is_empty():
            print("Nothing to purge")
            return

        print("*** #4: Add wildcards to purge list.")
        final_purge = self._add_wildcards_to_purge_list(
            initial_purge, artefacts.recent)
        _verify_purge_list(final_purge, artefacts.recent)

        print("\nFINAL PURGE LIST:")
        final_purge.prettyprint()
        return final_purge

    def do_purge(self, purge_list):
        print("""
        *** #5: Perform purge.
        """)
        if purge_list is None or purge_list.is_empty():
            print("Nothing to purge")
            return

        for gav in purge_list.gavs():
            self.nexus.delete_gav_and_its_assets(gav)

        print("""
        *** #6: Compact blobstore.
        """)

        self.nexus.compact_blobstore()

        print("""
        *** #7: Done.
        """)

    def _get_product_releases(self):
        recent = []
        stale = []
        for product in self.products:
            recent.extend(product.recent_releases())
            stale.extend(product.stale_releases())

        return ProductReleases(recent=recent, stale=stale)

    def _known_artefacts(self, artefacts):
        # Create list of all versions for named artefacts in recent and stale
        # (Ideally we would list all artefacts in nexus, but this breaks 10k limit)
        known = GAVtree("known")
        done = set()
        for tree in [artefacts.recent, artefacts.stale]:
            for groupId in tree._tree:
                for artefactId in tree._tree[groupId]:
                    key = (groupId, artefactId)
                    if key in done:
                        continue
                    for version in self.nexus.artefact_versions(
                            groupId, artefactId):
                        gav = GAV(groupId, artefactId, version)
                        known.add(gav)
                    done.add(key)
        return known

    def _create_initial_purge_list(self, artefacts):
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

            earliest_used = artefacts.recent.earliest_version(
                groupId, artefactId)
            must_keep = (not is_earlier_version(version, earliest_used))
            return must_keep

        def _add_to_purge_from_group(known, purge, groupId):
            for artefactId in known.artefacts(groupId):
                _add_to_purge_from_artefact(known, purge, groupId, artefactId)

        def _add_to_purge_from_artefact(known, purge, groupId, artefactId):

            if _must_keep_artefact(groupId, artefactId):
                return

            for version in known.versions(groupId, artefactId):
                if _must_keep_version(groupId, artefactId, version):
                    continue

                purge.add(GAV(groupId, artefactId, version))

        known = self._known_artefacts(artefacts)

        purge = GAVtree('purge')
        for groupId in known.groups():
            _add_to_purge_from_group(known, purge, groupId)

        # print("\tcreated initial purge list")
        print("initial: purge.has_version %s %s %s" %
              ('scot.mygov.housing', 'housing-data', '1.0.40'))
        return purge

    def _add_wildcards_to_purge_list(self, purge, recent):
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
                if not _has_related_artifacts(groupId, artifactId):
                    continue
                """
                delete wildcards w/ same groupId/version
                if '-deb', wildcards are all other artefacts with same versions
                if Beta, wildcards are as above with extra limitation that
                    artefactId must match '*authentication*'
                """
                for version in purge.versions(groupId, artifactId):
                    for artId in self.nexus.related_artefactIds(
                            groupId, version):

                        if _should_add_wildcard_artefact(
                                groupId, artId, version, self.nexus):

                            purge2.add(GAV(groupId, artId, version))
        return purge2


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


def _must_keep_artefact(groupId, artefactId):
    Snapshot = collections.namedtuple('Snapshot', ['group', 'artefact'])
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
            return True
    return False


def _print_gotten_artefacts(artefacts):
    print("\nARTEFACTS: ")
    artefacts.recent.prettyprint()
    artefacts.stale.prettyprint()


def _has_related_artifacts(groupId, artifactId):
    """
    >>> _has_related_artifacts('org.mygovscot.publishing', 'publishing-deb')
    True
    >>> _has_related_artifacts('org.mygovscot.beta', 'authentication-deb')
    True
    >>> _has_related_artifacts('org.mygovscot.beta', 'web-site')
    False
    """
    Beta = 'org.mygovscot.beta'
    if not (artifactId.endswith('-deb') or artifactId.endswith('-debian')):
        return False
    if groupId == Beta and artifactId != 'authentication-deb':
        return False
    return True


def _should_add_wildcard_artefact(groupId,
                                  artifactId,
                                  version=None,
                                  nexus=None):
    """
    >>> _should_add_wildcard_artefact('org.mygovscot.publishing', 'publishing-deb')
    no version for wildcard: org.mygovscot.publishing publishing-deb
    True
    >>> _should_add_wildcard_artefact('org.mygovscot.publishing', 'publishing-service')
    no version for wildcard: org.mygovscot.publishing publishing-service
    True
    >>> _should_add_wildcard_artefact('org.mygovscot.beta', 'authentication-deb')
    no version for wildcard: org.mygovscot.beta authentication-deb
    True
    >>> _should_add_wildcard_artefact('org.mygovscot.beta', 'authentication-service')
    no version for wildcard: org.mygovscot.beta authentication-service
    True
    >>> _should_add_wildcard_artefact('org.mygovscot.beta', 'web-site')
    False
    """

    Beta = 'org.mygovscot.beta'

    if groupId == Beta and artifactId.find('authentication') == -1:
        return False

    if _must_keep_artefact(groupId, artifactId):
        return False

    if version:
        gav = GAV(groupId, artifactId, version)
        if not gav.has_parent(nexus=nexus):
            print("Not adding wildcard for artefact with no parent: %s" % gav)
            return False
    else:
        print("no version for wildcard: %s %s" % (groupId, artifactId))

    return True


def _verify_purge_list(purge_list, recent):
    for gav in purge_list.gavs():
        assert (recent.has_version(gav) is False)


#
# eof
