import unittest
from intergraph import InterGraph
from cfg import CFG, Block
edges = {"a": ["d"],
                                "b": ["c", "d"],
                                "c": ["b", "d", "e"],
                                "d": ["a","b", "c", "e"],
                                "e": ["c", "d"]}
def is_simplicial(restriction, edges):
    neighbours = set()
    for node in edges[restriction[-1]]:
        if node in restriction:
            neighbours.add(node)
    
    for neighbour in neighbours:
        neighbours2 = {neighbour} 
        for neighbour2 in edges[neighbour]:
            if neighbour2 in restriction:
                neighbours2.add(neighbour2)
        
        # For every neighbour, we check that its neighbours is included
        # in the set of neighbours of the last element of the ordering
        if neighbours.intersection(neighbours2) != neighbours:
            print(neighbours, neighbours2)
            return False
    return True

def is_simplicial_order(SEO, edges):
    for i in range(1, len(SEO)):
        if not is_simplicial(SEO[:i], edges):
            return False
    return True

class max_card_search(unittest.TestCase):

    def setUp(self):
        cfg = CFG("Empty", None, [Block("lbl")])
        self.intergraph = InterGraph(cfg)
    
    def test_search_empty(self):
        SEO = self.intergraph.max_cardinality_search()
        self.assertEqual(SEO, [])
    
    def test_search_small(self):
        self.intergraph.nodes = {"a","b","c","d","e"}
        self.intergraph.edges = {"a": ["d"],
                                "b": ["c", "d"],
                                "c": ["b", "d", "e"],
                                "d": ["a","b", "c", "e"],
                                "e": ["c", "d"]}
        
        SEO = self.intergraph.max_cardinality_search()
        self.assertEqual(is_simplicial_order(SEO, self.intergraph.edges), True)
    
    def tearDown(self):
        del self.intergraph


if __name__ == "__main__":
    unittest.main()