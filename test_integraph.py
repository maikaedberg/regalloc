from json import load
import unittest
from intergraph import InterGraph
from cfg import CFG, Block
from tac import load_tac, Proc

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
            return False
    return True

def is_simplicial_order(SEO, edges):
    for i in range(1, len(SEO)):
        if not is_simplicial(SEO[:i], edges):
            return False
    return True

class max_card_search(unittest.TestCase):

    def setUp(self):
        tac = Proc("Empty", [], [])
        self.intergraph = InterGraph(tac)
    
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
        self.assertTrue(is_simplicial_order(SEO, self.intergraph.edges))
 
    def tearDown(self):
        del self.intergraph

class getAllocationRecord(unittest.TestCase):

    def setUp(self):
        tac = Proc("Empty", [], [])
        self.intergraph = InterGraph(tac)
    
    def test_allocation_empty(self):
        stack_size, alloc = self.intergraph.get_allocation_record()
        self.assertEqual(stack_size, 0)
        self.assertEqual(alloc, {})
    
    def test_allocation_small(self):
        self.intergraph.nodes = {"a","b","c","d","e"}
        self.intergraph.edges = {"a": ["d"],
                                "b": ["c", "d"],
                                "c": ["b", "d", "e"],
                                "d": ["a","b", "c", "e"],
                                "e": ["c", "d"]}
        self.intergraph.greedy_coloring()
        stacksize, alloc = self.intergraph.get_allocation_record()
        self.assertEqual(stacksize, 0)
        self.assertEqual(len(alloc), len(self.intergraph.nodes))

        for node in self.intergraph.nodes:
            for neighbour in self.intergraph.edges[node]:
                self.assertNotEqual(alloc[node], alloc[neighbour])
    
    def test_allocation_fib(self):
        fname = "./examples/fib.tac.json"
        tac = load_tac(fname)
        for decl in tac:
            if isinstance(decl, Proc):
                integraph = InterGraph(decl)
                integraph.greedy_coloring()
                stacksize, alloc = integraph.get_allocation_record()
                self.assertEqual(stacksize, 0)
                self.assertEqual(len(alloc), len(integraph.nodes))

                for node in self.intergraph.nodes:
                    for neighbour in self.intergraph.edges[node]:
                        self.assertNotEqual(alloc[node], alloc[neighbour])

    def tearDown(self):
        del self.intergraph

class testsOnFib(unittest.TestCase):
    def setUp(self):
        fname = "./examples/fib.tac.json"
        tac = load_tac(fname)
        self.fib = tac[0]
        self.main = tac[1]
    
    def test_MCS_fib(self):
        def test_SEO(proc):
            intergraph = InterGraph(proc)
            SEO = intergraph.max_cardinality_search()
            self.assertTrue(is_simplicial_order(SEO, intergraph.edges))

            del intergraph

        test_SEO(self.fib)
        test_SEO(self.main)
        
    def test_alloc_fib(self):
        def test_alloc(proc):
            intergraph = InterGraph(proc)
            intergraph.greedy_coloring()
            stacksize, alloc = intergraph.get_allocation_record()
            
            self.assertEqual(stacksize, 0)
            self.assertEqual(len(alloc), len(intergraph.nodes))

            for node in intergraph.nodes:
                for neighbour in intergraph.edges[node]:
                    self.assertNotEqual(alloc[node], alloc[neighbour])
            
            del intergraph
        
        test_alloc(self.fib)
        test_alloc(self.main)

if __name__ == "__main__":
    unittest.main()
