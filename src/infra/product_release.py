from .gav import GAV


class ProductRelease():
    def __init__(self, product, release):
        from .product import Product
        assert isinstance(product, Product)
        assert isinstance(release, int)
        self.product = product
        self.release = release  # this is the nexus 'version'
        self.group = 'scot.mygov.release'

    def __str__(self):
        return "%s:%s" % (self.product, self.release)

    def describe(self, label):
        return "  %s:\t%s\tJenkins build %s\n    %s\n" % (
            label, self.__str__(), self.jenkins_build_date,
            self.jenkins_build_console_url)

    @property
    def jenkins_build_date(self):
        if self.release is None:
            return None

        build_date = self.product.jenkins.build_date(self._jenkins_job_name,
                                                     self.release)
        return build_date

    @property
    def jenkins_build_console_url(self):
        url = self.product.jenkins.build_url(self._jenkins_job_name,
                                             self.release)
        url = url.replace("/api/json", "/console")
        return url

    @property
    def nexus_release_yaml(self):
        return self.product.nexus.product_release_yaml(
            self.group, self.product.name, self.release)

    def gavs(self):  # versioned artifacts
        gavs = set()
        jsn = self.nexus_release_yaml
        for x in jsn:
            try:
                art = jsn[x]
            except Exception as e:
                print("x = %s" % x)
                print("jsn = %s" % jsn)
                raise
            """
            example art:
            {
                'artefactId': 'trigger',
                'groupId': 'scot.mygov.rubric',
                'packaging': 'deb',
                'version': '1.0.48'
            }
            """
            assert art['packaging'] == 'deb'

            # note: artefact is British, artifact is US spelling
            gav = GAV(
                groupId=art['groupId'],
                artefactId=art['artifactId'],
                version=art['version'])
            gavs.add(gav)
        return frozenset(gavs)

    @property
    def _jenkins_job_name(self):
        _jobs = {
            'gov-site': "gov-release-prepare",
            'mygov-site': 'mygov-release-prepare',
        }
        return _jobs[self.product.name]


# eof
