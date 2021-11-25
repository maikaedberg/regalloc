from cfg import CFG

class InterGraph():
    def __init__(self, cfg):
        self.nodes = []
        self.edges = {}
        self.spilled = []
        self.build_graph(cfg)
    
    def build_graph(self, cfg):
        pass

    def max_cardinality_search(self):
        """Returns a SEO from the current interference graph"""
        pass

    def spill(self, temporary):
        pass

    def get_allocation_record(self):
        pass