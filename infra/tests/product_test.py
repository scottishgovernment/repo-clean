# from pdb import set_trace
from datetime import timedelta
from unittest.mock import Mock
from lxml import etree
from io import BytesIO

from infra.config import get_my_servers
from infra.jenkins import Jenkins
from infra.nexus import Nexus
from infra.product import Product
from infra.config import EARLIEST_RELEASE_DATE
from infra.gav import GAV

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


class MockNexus(Mock):
    def artefact_pom(self, gav):
        if gav.g == "scot.mygov.housing" and gav.a == "housing":
            xml = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
<modelVersion>4.0.0</modelVersion>
<parent>
<groupId>scot.mygov</groupId>
<artifactId>mygov-parent</artifactId>
<version>4</version>
</parent>
<groupId>scot.mygov.housing</groupId>
<artifactId>housing</artifactId>
<version>1.0.99</version>
<packaging>pom</packaging>
<name>Housing</name>
<scm>
<connection>
scm:git:ssh://git@stash.digital.gov.uk:7999/mgv/housing.git
</connection>
<url>
http://stash.digital.gov.uk/projects/MGV/repos/housing/
</url>
</scm>
<modules>
<module>housing-service</module>
<module>housing-deb</module>
</modules>
</project>"""
        else:
            raise RuntimeError("test:artefact.pom needs data for %s" % gav)
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

    def test_gav_has_parent(self):
        gav = GAV("scot.mygov.housing", "housing", "1.0.99")
        nexus = MockNexus(spec=Nexus)
        assert gav.has_parent(nexus)


if __name__ == '__main__':
    tp = TestProduct()
    tp.test_is_recent_release()

# eof
