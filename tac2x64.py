import sys
from stack import Stack
import json
import os

def gen_dealloc():
    """
    Returns assembly code for deallocation
    """
    return [".Lexit:",
            "\tmovq %rbp, %rsp",
            "\tpopq %rbp",
            "\tretq"]

binops = {'add': 'addq',
          'sub': 'subq',
          'mul': (lambda ra, rb, rd: [f'movq {ra}, %rax',
                                      f'imulq {rb}',
                                      f'movq %rax, {rd}']),
          'div': (lambda ra, rb, rd: [f'movq {ra}, %rax',
                                      f'cqto',
                                      f'idivq {rb}',
                                      f'movq %rax, {rd}']),
          'mod': (lambda ra, rb, rd: [f'movq {ra}, %rax',
                                      f'cqto',
                                      f'idivq {rb}',
                                      f'movq %rdx, {rd}']),
          'and': 'andq',
          'or': 'orq',
          'xor': 'xorq',
          'shl': (lambda ra, rb, rd: [f'movq {ra}, %r11',
                                      f'movq {rb}, %rcx',
                                      f'salq %cl, %r11',
                                      f'movq %r11, {rd}']),
          'shr': (lambda ra, rb, rd: [f'movq {ra}, %r11',
                                      f'movq {rb}, %rcx',
                                      f'sarq %cl, %r11',
                                      f'movq %r11, {rd}'])}
unops = {'neg': 'negq',
         'not': 'notq'}

cond_jumps = {'jz', 'jnz', 'jl', 'jnl', 'jle', 'jnle'}

first_six_args = { 1 : (lambda ra: [f'movq {ra}, %rdi'] ),
                   2 : (lambda ra: [f'movq {ra}, %rsi'] ),
                   3 : (lambda ra: [f'movq {ra}, %rdx'] ),
                   4 : (lambda ra: [f'movq {ra}, %rcx'] ),
                   5 : (lambda ra: [f'movq {ra}, %r8'] ),
                   6 : (lambda ra: [f'movq {ra}, %r9'] )}

def tacinstr_to_asm(stack, opcode, args, result):

    asm = []

    if opcode == 'nop':
        pass

    elif opcode == 'const':
        assert len(args) == 1 and isinstance(args[0], int)
        asm.append(f'\tmovq ${args[0]}, {stack[result]}')

    elif opcode == 'copy':
        assert len(args) == 1
        asm.append(f'\tmovq {stack[args[0]]}, %r11')
        asm.append(f'\tmovq %r11, {stack[result]}')

    elif opcode in binops:
        assert len(args) == 2
        proc = binops[opcode]
        if isinstance(proc, str):
            asm.extend([f'\tmovq {stack[args[0]]}, %r11',
                        f'\t{proc} {stack[args[1]]}, %r11',
                        f'\tmovq %r11, {stack[result]}'])
        else:
            for i in proc(stack[args[0]], stack[args[1]], stack[result]):
                asm.append('\t' + i)

    elif opcode in unops:
        assert len(args) == 1
        proc = unops[opcode]
        asm.extend([f'\tmovq {stack[args[0]]}, %r11',
                    f'\t{proc} %r11',
                    f'\tmovq %r11, {stack[result]}'])

    elif opcode == 'call':
        assert len(args) == 2
        assert args[0][0] == "@"

        if args[1] > 6 and args[1] % 2 == 1:
            no_args = args[1] + 1
            stack.extra_params[no_args] = stack.extra_params[no_args - 1]
        else:
            no_args = args[1]

        for N in range(no_args, 6, -1):
            asm.append(f'\tpushq {stack[stack.extra_params[N]]}')
        
        asm.append(f'\tcallq {args[0].lstrip("@")}')

        e_param = no_args - 6
        if e_param > 0:
            asm.append(f'\taddq ${8* e_param}, %rsp')
        
        if result is not None:
            asm.append(f'\tmovq %rax, {stack[result]}')
        
        for r in reversed(stack.alloc_reg):
            asm.append(f'\tpopq {r[1:]}')
        
    elif opcode == 'label':
        assert len(args) == 1 and result == None
        assert args[0][1:3] == ".L"
        asm.append(f'.L{stack.name}{args[0][3:]}:')


    elif opcode == 'jmp':
        assert len(args) == 1 and result == None
        assert args[0][1:3] == ".L"
        asm.append(f'\tjmp .L{stack.name}{args[0][3:]} ')

    elif opcode in cond_jumps:
        assert len(args) == 2
        assert args[1][1:3] == ".L"
        asm.extend([f'\tmovq {stack[args[0]]}, %r11',
                    f'\tcmpq $0, %r11',
                    f'\t{opcode} .L{stack.name}{args[1][3:]}'])
    
    elif opcode == 'param':
        assert len(args) == 2 and result == None

        if args[0] == 1:
            for r in stack.alloc_reg:
                asm.append(f'\tpushq {r[1:]}')

        if args[0] <= 6:
            proc = first_six_args[args[0]]
            for instrucs in proc(stack[args[1]]):
                asm.append('\t' + instrucs)
        else:
            stack.extra_params[args[0]] = args[1]

    elif opcode == 'ret':
        if args == []: # VOID RET
            asm += ['\txorq %rax, %rax', '\tjmp .Lexit']
        else:
            assert len(args) == 1
            asm += [f'\tmovq {stack[args[0]]}, %rax', '\tjmp .Lexit']

    return asm

def tac_to_asm_f(file):
    with open(file, "r") as f:
        js_obj = json.load(f)

    global_vars = []
    stacks = []

    for decls in js_obj:
        if "var" in decls:
            global_vars.append((decls["var"][1:], decls["init"]))
        elif "proc" in decls:
            stack = Stack(decls)
            for instr in decls["body"]:
                stack.asm += tacinstr_to_asm(stack, instr['opcode'], instr['args'], instr['result'])
            stacks.append(stack)
        else:
            print(f"Unrecognized type {decls}")
            sys.exit(1)

    asm = []

    for var, val in global_vars:
        asm += [f'\t.globl {var}', '\t.data', f'{var}: .quad {val}']

    for stack in stacks:
        asm += stack.gen_alloc()
        asm += stack.asm
    
    asm += gen_dealloc()

    return asm

def compile_tac(asm, fname):
    if fname.endswith('.tac.json'):
        rname = fname[:-9]

    elif fname.endswith('.json'):
        rname = fname[:-5]

    elif fname.endswith('.bx'):
        rname = fname[:-3]

    else:
        raise ValueError(f'{fname} does not end in .tac.json, .json or .bx')

    xname = rname + '.exe'
    sname = rname + '.s'
    with open(sname, 'w') as afp:
        print(*asm, file=afp, sep='\n')
    # print(f'{fname} -> {sname}')
    os.system(f'gcc -g -o {xname} {sname} bx_runtime.c')
    # print(f'{sname} -> {xname}')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} tacfile.tac.json')
        sys.exit(1)
    fname = sys.argv[1]
    asm = tac_to_asm_f(fname)
    compile_tac(asm, fname)
