first_six_args = { 1 : (lambda ra: [f'\tmovq %rdi, {ra}'] ),
                   2 : (lambda ra: [f'\tmovq %rsi, {ra}'] ),
                   3 : (lambda ra: [f'\tmovq %rdx, {ra}'] ),
                   4 : (lambda ra: [f'\tmovq %rcx, {ra}'] ),
                   5 : (lambda ra: [f'\tmovq %r8, {ra}'] ),
                   6 : (lambda ra: [f'\tmovq %r9, {ra}'] )}
class Stack():
    """
    Class representing a stack storing a map from tac temporaries to stack
    slots indexed by rbp
    """
    def __init__(self, tac):
        self.tac = tac
        self.name = tac["proc"][1:]
        self.asm = []
        self.temp_map = {}
        self.stacksize = tac["stacksize"]
        self.alloc = tac["alloc"]
        self.temp_count = 0
        self.rsp = "%rbp"
        self.load_temp_map()

        self.extra_params = {}

    def load_temp_map(self):
        """
        Initialize temp_map by going through all lines in tac
        """
        assert "proc" in self.tac
        
        for i in range(len(self.tac["args"])):
            arg = self.tac["args"][i]
            if i < 6:
                self.temp_count += 1
                reg = f"{-8 * self.temp_count}(%rbp)"
                self.asm += first_six_args[i + 1](reg)
                self.temp_map[arg] = reg
            else:
                assert 8* (i - 4) != 0
                assert 8* (i - 4) != 8
                assert 8* (i - 4) < self.stacksize
                self.temp_map[arg] = f"{8* (i - 4)}(%rbp)"

        body = self.tac["body"]
        for code in body:
            try:
                temp = code["result"]
            except KeyError:
                print(code)
            if temp in self.alloc:
                self.temp_map[temp] = self.alloc[temp][1:]
            elif temp is not None and temp[0] == '%' and temp[1:].isnumeric():
                if temp not in self.temp_map.keys():
                    self.temp_count += 1
                    assert -8 * self.temp_count < self.stacksize
                    self.temp_map[temp] = f"{-8 * self.temp_count}(%rbp)"

        self.rsp = f"{-8 * (self.temp_count+1)}(%rbp)"
        
    def __getitem__(self, key):
        if key[0] == "@":
            return key[1:]
        return self.temp_map[key]

    def gen_alloc(self):
        """
        Generates assembly code for stack allocation where stack slots are
        in units of 8 bytes
        """
        res = ["\n",
               f"\t.global {self.name}",
                "\t.text",
               f"{self.name}:",
                "\tpushq %rbp",
                "\tmovq %rsp, %rbp"]
        

        rounded_up = (self.temp_count + 7) & (-8)
        res.append(f"\tsubq ${rounded_up * 8}, %rsp")
        return res

