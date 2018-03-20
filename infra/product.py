from .config import EARLIEST_RELEASE_DATE
from .config import my_servers
from .product_release import ProductRelease
from .jenkins import Jenkins
from .nexus import Nexus


class Product():
    def __init__(self, name, earliest_release_date=EARLIEST_RELEASE_DATE):
        self.name = name
        self.earliest_release_date = earliest_release_date
        self._recent_releases = None
        self._stale_releases = None
        self.jenkins = Jenkins(my_servers['JENKINS'])
        self.nexus = Nexus(my_servers['NEXUS'])

    def __str__(self):
        return self.name

    # @property
    # def _jobs(self):
    #     return {
    #         'gov-site': "gov-release-prepare",
    #         'mygov-site': 'mygov-release-prepare',
    #     }
    #
    # @property
    # def _job_name(self):
    #     return self._jobs[self.name]

    def _is_recent_release(self, version):
        pr = ProductRelease(product=self, release=version)
        recent = (pr.jenkins_build_date >= self.earliest_release_date)
        return recent

    def _is_day_0_release(self, version):
        pr = ProductRelease(product=self, release=version)
        return pr.jenkins_build_date == EARLIEST_RELEASE_DATE

    def _make_recent_and_stale(self):

        tree = self.nexus.product_maven_metadata(self.name)

        current = int(tree.findtext('versioning/release'))
        sorted_versions = _get_sorted_versions(tree)
        recent = []
        stale = []

        for version in sorted_versions:
            if self._is_recent_release(version):
                recent.append(version)
            else:
                stale.append(version)

        # If a release was not made on the start of the period we are
        # interested in, then we need to keep the latest stale one,
        # because that was the one in use on the start date.

        if len(recent) and not self._is_day_0_release(recent[0]):
            oldest_stale_version = stale[-1]
            recent.insert(0, oldest_stale_version)
            stale.remove(oldest_stale_version)

        # Store the results

        self._recent_releases = recent
        self._stale_releases = stale

        earliest = (recent[0] if recent else None)

        print("%s" % self.name)
        print(
            ProductRelease(product=self,
                           release=current).describe("Current Release"))
        print(
            ProductRelease(product=self,
                           release=earliest).describe("Earliest Release"))

        # if self.args.verbose:
        #     print("recent : %s" % self._recent_releases)
        #     print("stale  : %s" % self._stale_releases)

    def recent_releases(self):
        if self._recent_releases is None:
            self._make_recent_and_stale()
        return [
            ProductRelease(product=self, release=x)
            for x in self._recent_releases
        ]

    def stale_releases(self):
        if self._stale_releases is None:
            self._make_recent_and_stale()
        return [
            ProductRelease(product=self, release=x)
            for x in self._stale_releases
        ]


def _get_sorted_versions(tree):
    versions = tree.findall('versioning/versions/version')
    try:
        int_versions = [int(x.text) for x in versions]
    except Exception:
        raise RuntimeError("Handle non-int versions: %s" % versions)
    sorted_versions = sorted(int_versions)
    return sorted_versions


# eof
