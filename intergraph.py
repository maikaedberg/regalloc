from cfg import CFG, recompute_liveness, infer

col_to_reg = {1: '%%rax', 2: '%%rdi', 3: '%%rsi', 4: '%%rdx', 5: '%%rcx',
              6:'%%r8', 7:'%%r9', 8:'%%r10', 9: '%%rbx', 10:'%%r12', 
              11:'%%r13', 12:'%%r14', 13:'%%r15'}
              
class InterGraph():
    def __init__(self, tlv, cfg = None):
        self.nodes = set()
        if cfg is None:
            self.cfg = infer(tlv)
        else:
            self.cfg = cfg

        self.edges = {}
        self.build_edges(self.cfg)
        self.spilled = []
        
        self.og_color = dict()
        self.pre_color(tlv)
        self.color = dict()

    def build_edges(self, cfg):
        livein, liveout = dict(), dict()
        recompute_liveness(cfg, livein, liveout)

        for instr in cfg.instrs():
            if instr.opcode == 'copy':
                # use(I) = I.arg1, def(I) = I.dest
                self.nodes.add(instr.arg1)
                self.nodes.add(instr.dest)
                self.edges.setdefault(instr.arg1, set())
                self.edges.setdefault(instr.dest, set())
                for x in liveout[instr]:
                    self.nodes.add(x)
                    self.edges.setdefault(x, set())
                    if x != instr.arg1:
                        self.edges[x].add(instr.arg1)
                        self.edges[instr.arg1].add(x)
                    if x != instr.dest:
                        self.edges[x].add(instr.dest)
                        self.edges[instr.dest].add(x)
            else:
                for x in liveout[instr]:
                    self.nodes.add(x)
                    self.edges.setdefault(x, set())
                    for y in instr.defs():
                        self.nodes.add(y)
                        self.edges.setdefault(y, set())
                        if y != x:
                            self.edges[x].add(y)
                            self.edges[y].add(x)

    def pre_color(self, tlv):
        for i in range(min(len(tlv.t_args), 6)):
            self.og_color[tlv.t_args[i]] = i + 2

        for i in range(1, len(tlv.body), -1):
            if tlv.body[-1].opcode == 'ret':
                if tlv.body[-1].dest is not None:
                    self.og_color[1] = i
                break
            
    def max_cardinality_search(self):
        """Returns a SEO from the current interference graph"""
        vertex = None
        # Get one element from the set
        for node in self.nodes:
            vertex = node
            break

        if vertex is None:
            return []

        SEO = [vertex]
        cards = {v : 0 for v in self.edges if v != vertex}

        while len(SEO) < len(self.nodes):
            for v in self.edges[SEO[-1]]:
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
            col = self.og_color.copy()

        seo = self.max_cardinality_search()

        for u in self.nodes:
            if u not in col: 
                col[u] = 0
                
        for v in seo:
            if v[:2] == "%%":
                for color, reg in col_to_reg.items():
                    if reg == v:
                        col[v] = color

        for v in seo:
            if col[v] != 0:
                continue

            visited = set()
            for nghb in self.edges[v]:
                visited.add(col[nghb])

            argmin = 1
            while argmin in visited:
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
        if len(self.color) == 0:
            return
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
        
        self.greedy_coloring()
        self.spill()

        for vertex, color in self.color.items():
            if vertex[:2] == "%%":
                continue
            alloc[vertex] = col_to_reg[color]
        for i in range(len(self.spilled)):
            alloc[self.spilled[i]] = -(i + 1) * 8

        return (stack_size, alloc)
    
    def register_coalesce(self):
        cfg=self.cfg
        for instr in cfg.instrs():
            if instr.opcode=='copy':
                src=instr.arg1
                dest=instr.dest
                
                if self.color(src)==self.color(dest):
                    cfg.remove_instr(instr) #needs to be added
                elif src not in self.next(dest) and len(self.compute_free(src,dest)>0):
                    c=new_temp() #new temp s.t. col(%c) = c, c in compute free 
                    
                    self.new_connect(src, c)
                    self.new_connect(dest, c)
                    self.delete_node(src), self.delete_node(dest)
                    cfg.propogate(src, c)
                    cfg.propogate(dest, c)
                    self.build_edges(cfg)
                    
                    
    def new_connect(self, v, new):
        nbors=self.next(v)
        for a in nbors:
            self.edges[a].add(new)    
    
    def compute_free(self,a,b):
        res=set()
        for u in self.color:
            if u in self.next(a) or u in self.next(b):
                res.add(self.color[u])
        return res
    
    # def is_redundant_copy(self, instr) -> bool:
    #     src=instr.arg1
    #     dest=instr.dest
    #     return (instr.opcode=='copy' and src!=dest and self.color(src)!=self.color(dest))
    
    def delete_node(self, v):
        for k,target in self.edges:
            if v in target:
                self.edges[k].remove(v)
        self.nodes.remove(v)
            
    def next(self, v):
        return set(self.edges[v])
   

# ------------------------------------------------------------------------------
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