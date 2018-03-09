# from pdb import set_trace
from datetime import timedelta
from unittest.mock import Mock
from lxml import etree
from io import BytesIO

from infra.config import get_my_servers
from infra.jenkins import Jenkins
from infra.nexus import Nexus
from infra.product import Product
from infra import EARLIEST_RELEASE_DATE

get_my_servers()

VERSION_MINUS_2 = 98
VERSION_MINUS_1 = 99
VERSION_0 = 100
VERSION_PLUS_1 = 101
VERSION_PLUS_2 = 102

DAY_MINUS_2 = {VERSION_MINUS_2: EARLIEST_RELEASE_DATE - timedelta(days=2)}
DAY_MINUS_1 = {VERSION_MINUS_1: EARLIEST_RELEASE_DATE - timedelta(days=1)}
DAY_0 = {VERSION_0: EARLIEST_RELEASE_DATE}
DAY_PLUS_1 = {VERSION_PLUS_1: EARLIEST_RELEASE_DATE + timedelta(days=1)}
DAY_PLUS_2 = {VERSION_PLUS_2: EARLIEST_RELEASE_DATE + timedelta(days=2)}


class MockJenkins(Mock):
    """Mock version of Jenkins for testing without network access."""

    def build_date(self, job_name, version):
        """Replace the build_date obtained from the maven metadata."""
        release_dates = {
            'gov-release-prepare': {
                **DAY_MINUS_1,
                **DAY_0,
                **DAY_PLUS_1,
            }
        }
        return release_dates[job_name][version]


class MockJenkins_with_gaps(Mock):
    """Mock version of Jenkins for testing without network access."""

    def build_date(self, job_name, version):
        """Replace the build_date obtained from the maven metadata."""
        release_dates = {
            'gov-release-prepare': {
                **DAY_MINUS_2,
                **DAY_MINUS_1,
                **DAY_PLUS_1,
            },
        }

        return release_dates[job_name][version]


class MockNexus_with_gaps(Mock):
    def product_maven_metadata(self, component_name):
        assert component_name == "gov-site"
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<metadata>
  <groupId>scot.mygov.release</groupId>
  <artifactId>gov-site</artifactId>
  <versioning>
    <release>%s</release>
    <versions>
      <version>%s</version>
      <version>%s</version>
      <version>%s</version>
    </versions>
    <lastUpdated>20180220133929</lastUpdated>
  </versioning>
</metadata>""" % (VERSION_PLUS_1, VERSION_MINUS_2, VERSION_MINUS_1,
                  VERSION_PLUS_1)
        tree = etree.parse(BytesIO(xml.encode('utf8')))
        return tree


class TestProduct(object):
    """Test the Product class."""

    def test_product_release_versions(self):
        product = Product('gov-site')
        product.jenkins = MockJenkins(spec=Jenkins)
        assert (product._is_recent_release(version=VERSION_MINUS_1) is False)
        assert (product._is_recent_release(version=VERSION_0) is True)
        assert (product._is_recent_release(version=VERSION_PLUS_1) is True)

    def test_product_release_versions_with_gaps(self):
        product = Product('gov-site')
        product.jenkins = MockJenkins_with_gaps(spec=Jenkins)
        assert (product._is_recent_release(version=VERSION_MINUS_2) is False)
        assert (product._is_recent_release(version=VERSION_MINUS_1) is False)
        assert (product._is_recent_release(version=VERSION_PLUS_1) is True)

    def test_product_recent_and_stale(self):
        product = Product('gov-site')
        product.jenkins = MockJenkins_with_gaps(spec=Jenkins)
        product.nexus = MockNexus_with_gaps(spec=Nexus)

        product._make_recent_and_stale()
        assert (product._recent_releases == [
            VERSION_MINUS_1,
            VERSION_PLUS_1,
        ])
        assert (product._stale_releases == [
            VERSION_MINUS_2,
        ])


if __name__ == '__main__':
    tp = TestProduct()
    tp.test_is_recent_release()

# eof
