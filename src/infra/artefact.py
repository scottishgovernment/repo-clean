class Artefact():

    def __init__(self, groupId, artefactId):
        self.groupId = groupId
        self.artefactId = artefactId

    def __str__(self):
        return "%s:%s" % (self.groupId, self.artefactId)


# eof
