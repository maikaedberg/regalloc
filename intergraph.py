from cfg import CFG

class InterGraph():
    def __init__(self, cfg):
        self.nodes = ['c','b','a','d']
        self.edges = {'a' : [], 'b' : [], 'c' : ['d'], 'd' : ['c']}
        self.spilled = []
        self.build_graph(cfg)
    
    def build_graph(self, cfg):
        pass

    def max_cardinality_search(self):
        """Returns a SEO from the current interference graph"""

        vertex = self.nodes[0]
        SEO = [vertex]
        cards = {v : 0 for v in self.edges if v != vertex}

        while len(SEO) < len(self.nodes):
            for v in self.edges[vertex]:
                if v in cards:
                    cards[v] += 1
            v_max = max(cards, key = cards.get)
            SEO.append(v_max)
            cards.pop(v_max)

        return SEO


    def spill(self, temporary):
        pass

    def get_allocation_record(self):
        pass