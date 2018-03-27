from pdb import set_trace

from infra.gav_tree import GAVtree
from infra.gav import GAV


class TestGavTree(object):
    """Test the GavTree class."""

    def test_gav_tree_versions(self):
        gt = GAVtree('testing')
        ok1 = GAV('g', 'a', '1')
        ok2 = GAV('g', 'a', '2')
        ok3 = GAV('g', 'a', '3')
        bad1 = GAV('g', 'a', '99')
        gt.add(ok1)
        gt.add(ok2)
        gt.add(ok3)
        assert gt.has_version(ok1)
        assert not gt.has_version(bad1)


# eof
