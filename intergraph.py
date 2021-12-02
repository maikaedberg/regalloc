from cfg import CFG, recompute_liveness

class InterGraph():
    def __init__(self, cfg):
        self.nodes = set()
        self.edges = {}
        self.build_edges(cfg)
        self.spilled = []
        
        self.og_color = dict()

    def build_edges(self, cfg):
        livein, liveout = dict(), dict()
        recompute_liveness(cfg, livein, liveout)
        for instr in cfg.instrs:
            if instr.opcode == 'copy':
                for x in liveout[instr]:
                    self.edges.setdefault(x, []) + [instr.arg1 + instr.dest]
                    self.edges.setdefault(instr.arg1, []).append(x)
                    self.edges.setdefault(instr.dest, []).append(x)
                    self.nodes.add(x)
                self.nodes.add(instr.arg1)
                self.nodes.add(instr.dest)
            else:
                for x in liveout[instr]:
                    self.edges.setdefault(x, []).append(instr.dest)
                    self.edges.setdefault(instr.dest, []).append(x)
                    self.nodes.add(x)
                self.nodes.add(instr.dest)

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

    def greedy_coloring(self, col : dict()):

        seo = self.max_cardinality_search()

        for u in self.nodes:
            col.set_default(u, 0)
        for v in seo:
            if col[v] != 0:
                continue
            argmin = 1
            visited = set()
            for nghb in self.edges[v]:
                visited.add(col[nghb])
                while(argmin in visited):
                    argmin += 1
            col[v] = argmin

        return col            

    def spill(self, col):

        spill = max(col, key = col.get)
        if col[spill] <= 13:
            return

        self.nodes.remove(spill)
        del self.edges[spill]
        for nghbs in self.edges.values():
            try:
                nghbs.remove(spill)
            except ValueError:
                pass
        self.spilled.append(spill)

        col = self.greedy_coloring(self.og_color)
        self.spill(col)

    def get_allocation_record(self):
        alloc = dict()

        stack_size = len(self.spilled) * 8
        col_to_reg = {1: '%%rax', 2: '%%rcx', 3:'%%rdx', 4:'%%rsi', 5:'%%rdi', 
                      6:'%%r8', 7:'%%r9', 8:'%%r10', 9: '%%rbx', 10:'%%r12', 
                      11:'%%r13', 12:'%%r14', 13:'%%r15'}
                  
        col = self.spill(self.og_color)

        for vertex, color in col.items():
            alloc[vertex] = col_to_reg[color]
        for i in range(len(self.spilled)):
            alloc[self.spilled[i]] = -(i + 1) * 8

        return (stack_size, alloc)
            
