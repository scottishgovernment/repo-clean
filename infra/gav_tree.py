from functools import cmp_to_key

from .gav import GAV
from .utils import version_compare


class GAVtree():
    def __init__(self, name):
        self.name = name
        self._tree = {}

    def prettyprint(self):
        print()
        print("%s: " % self.name)
        for group in sorted(self._tree):
            print()
            print(group)
            for art in sorted(self._tree[group]):
                print("\t%s: %s" % (art, self._tree[group][art]))
        print()

    def add(self, gav):
        assert isinstance(gav, GAV)

        # abbreviate for clarity
        (g, a, v) = gav.abbrevs

        if not self.has_group(g):
            self._add_group(g)

        if not self.has_artefact(g, a):
            self._add_artefact(g, a)

        self._add_version(g, a, v)

    def contains(self, gav):
        assert isinstance(gav, GAV)

        (g, a, v) = gav.abbrevs
        return self.has_version(g, a, v)

    def groups(self):
        return self._tree.keys()

    def artefacts(self, groupId):
        return self._tree[groupId].keys()

    def versions(self, groupId, artefactId):
        return self._tree[groupId][artefactId]

    def _add_group(self, g):
        self._tree[g] = {}

    def _add_artefact(self, g, a):
        self._tree[g][a] = []

    def _add_version(self, g, a, v):
        versions = self._tree[g][a]
        versions.append(v)
        versions = list(set(versions))
        versions = sorted(versions, key=cmp_to_key(version_compare))
        self._tree[g][a] = versions

    def earliest_version(self, groupId, artefactId):
        versions = self.versions(groupId, artefactId)
        return (versions[0] if versions else None)

    def has_group(self, g):
        return g in self._tree.keys()

    def has_artefact(self, g, a):
        return self.has_group(g) and a in self._tree[g].keys()

    # def has_version(self, g, a, v):
    #     return self.has_artefact(g, a) and v in self._tree[g].versions

    def has_version(self, gav):
        return (
            self.has_artefact(gav.g, gav.a)
            and gav.v in self.versions(gav.g, gav.a))  # _tree[gav.g].versions)

    def gavs(self):
        for g in self.groups():
            for a in self.artefacts(g):
                for v in self.versions(g, a):
                    yield (GAV(g, a, v))

    def is_empty(self):
        return (len(self.groups()) == 0)


# eof
