from cfg import CFG, recompute_liveness, infer

class InterGraph():
    def __init__(self, tlv):
        self.nodes = set()

        self.cfg = infer(tlv)
        self.edges = {}
        self.build_edges(self.cfg)
        self.spilled = []
        
        self.og_color = dict()
        self.color = dict()

    def pre_color(tlv):
        pre_color = dict()
        for i in range(max(len(tlv.t_args), 6)):
            pre_color[i + 2] = tlv.t_args[i]
        assert tlv.body[-1].opcode == 'ret'
        if tlv.body[-1].dest is not None:
            pre_color[i] = 1

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
    def pre_color(tlv):
        pre_color = dict()
        for i in range(max(len(tlv.t_args), 6)):
            pre_color[i + 2] = tlv.t_args[i]
        assert tlv.body[-1].opcode == 'ret'
        if tlv.body[-1].dest is not None:
            pre_color[i] = 1
            
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

    def greedy_coloring(self, col=None):
        """
        Performs greedy coloring on either a given coloring or
        on the pre-coloring if none is specified
        Updates self.color with the result
        """
        if col is None:
            col = self.og_color

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

        self.color = col            

    def spill(self):
        """ 
        Spill a temporary if the number of colours currently in the 
        coloring is strictly greater than 13.
        Spilling involves adding the temporary to the spilled set and
        disconetting it from the graph.
        We spill the temporary with the largest colour.
        """
        spill = max(self.color, key = self.color.get)
        if self.color[spill] <= 13:
            return

        self.nodes.remove(spill)
        del self.edges[spill]
        for nghbs in self.edges.values():
            try:
                nghbs.remove(spill)
            except ValueError:
                pass
        self.spilled.append(spill)

        self.greedy_coloring()
        self.spill()

    def get_allocation_record(self):
        """
        Returns a tuple composed of the stack size and the allocation record
        """
        alloc = dict()

        stack_size = len(self.spilled) * 8
        col_to_reg = {1: '%%rax', 2: '%%rdi', 3: '%%rsi', 4: '%%rdx', 5: '%%rcx',
                      6:'%%r8', 7:'%%r9', 8:'%%r10', 9: '%%rbx', 10:'%%r12', 
                      11:'%%r13', 12:'%%r14', 13:'%%r15'}
        
        self.greedy_coloring()
        self.spill()

        for vertex, color in self.color.items():
            alloc[vertex] = col_to_reg[color]
        for i in range(len(self.spilled)):
            alloc[self.spilled[i]] = -(i + 1) * 8

        return (stack_size, alloc)
            
