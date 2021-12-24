from json import load
import unittest
from intergraph import InterGraph, is_simplicial_order
from tac import load_tac, Proc
from tac2etac import compute_SSA


def count_temporaries(set_):
    count = 0
    for elem in set_:
        if elem[:2] != "%%":
            count += 1
    return count

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

class testOnSimpleLoop(unittest.TestCase):
    def setUp(self):
        fname = "./examples/simple_loop.tac.json"
        tac = load_tac(fname)
        self.main = tac[0]
        self.cfg = compute_SSA(self.main)
    
    def test_alloc_loop(self):
        intergraph = InterGraph(self.main, self.cfg)
        intergraph.greedy_coloring()
        stacksize, alloc = intergraph.get_allocation_record()

        self.assertEqual(stacksize, 0)
        self.assertEqual(len(alloc), count_temporaries(intergraph.nodes))

        for node in intergraph.nodes:
            if node[:2] == "%%":
                continue
            for neighbour in intergraph.edges[node]:
                if neighbour[:2] == "%%":
                    continue
                self.assertNotEqual(alloc[node], alloc[neighbour])
        
        del intergraph

    def test_MCS_simple_loop(self):
        intergraph = InterGraph(self.main, self.cfg)
        SEO = intergraph.max_cardinality_search()
        self.assertTrue(is_simplicial_order(SEO, intergraph.edges))

        del intergraph

if __name__ == "__main__":
    unittest.main()
