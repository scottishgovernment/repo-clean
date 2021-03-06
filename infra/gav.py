class GAV():
    def __init__(self, groupId, artefactId, version):
        self.groupId = groupId
        self.artefactId = artefactId
        self.version = version

    def __str__(self):
        return "%s:%s:%s" % (self.groupId, self.artefactId, self.version)

    #
    # abbreviations for clarity
    #

    @property
    def g(self):
        return self.groupId

    @property
    def a(self):
        return self.artefactId

    @property
    def v(self):
        return self.version

    @property
    def abbrevs(self):
        return (self.g, self.a, self.v)

    def has_parent(self, nexus):
        xml = nexus.artefact_pom(self)
        parent = xml.find('{http://maven.apache.org/POM/4.0.0}parent')
        return (parent is not None)


# eof
