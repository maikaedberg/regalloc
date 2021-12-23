import argparse
import json
import os
from tac import load_tac, Proc, Instr
from tac2x64 import tac_to_asm

def emit(a, b, label, proc):
    """
    place b = copy a in the last instruction of the block that starts with label
    """
    for i, instr in enumerate(proc.body):
        if instr.opcode == "label" and instr.arg1 == label:
            beginning = i
            break
    end = beginning

    while proc.body[end].opcode[0] != "j" and proc.body[end].opcode != "ret":
        end += 1
    
    copy = Instr(b, "copy", [a])
    proc.body.insert(end, copy)

def fresh(temp_counter):
    return f"%dummy.{temp_counter}"

def destruct_ssa(proc):
    temp_counter = 0
    phis = []
    new = True
    for instr in proc.body:
        if instr.opcode == "phi":
            if new:
                phis.append([instr])
                new = False
            else:
                phis[-1].append(instr)
        else:
            new = True
    
    for phi_l in phis:
        correspondences = dict()
        to = set()
        from_ = set()
        cyclic = set()
        for instr in phi_l:
            to.add(instr.dest)
            for label, temp in instr.arg1.items():
                correspondences.setdefault(instr.dest, []).append((label, temp))
                from_.add(temp)
    
        for b, a_list in correspondences.copy().items():
            for label, a in a_list.copy():
                if a not in to:
                    a_list.remove((label, a))
                    emit(a, b, label, proc)
                else:
                    cyclic.add((label, a))
            if correspondences[b] == []:
                del correspondences[b]
        
        while len(correspondences) > 1:
            x = fresh(temp_counter)
            temp_counter += 1

            for b, a_list in correspondences.items():
                label_, a = a_list[0]
                emit(a, x, label_, proc)
                break
            
            for b, a_list in correspondences.copy().items():
                for (label, a2) in a_list:
                    if a2 == a:
                        a_list.remove((label, a2))
                        emit(x, b, label, proc)

                if correspondences[b] == []:
                    del correspondences[b]
        
        if len(correspondences) == 1:
            for b, a_list in correspondences.items():
                for (label, a) in a_list:
                    emit(a, b, label, proc)
    
    proc.body = [i for i in proc.body if i.opcode != "phi"]

        
if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Accepts a TAC file and produces ETAC with allocation records"
    )
    argparser.add_argument("source_path", help="path to TAC file in JSON or text", type=str)
    argparser.add_argument(
        "-o",
        help="Allows to specify output file name for the optimized TAC",
    )

    args = argparser.parse_args()
    source_path = args.source_path
    output_path = args.o

    tac_decls = load_tac(source_path)
    for decl in tac_decls:
        if isinstance(decl, Proc):
            destruct_ssa(decl)
    
    js_obj = [decl.js_obj for decl in tac_decls]
    asm = tac_to_asm(js_obj)

    rname = source_path[:-10]
    xname = rname + '.exe'
    sname = rname + '.s'
    with open(sname, 'w') as afp:
        print(*asm, file=afp, sep='\n')
    # print(f'{fname} -> {sname}')
    os.system(f'gcc -g -o {xname} {sname} bx_runtime.c')
    # print(f'{sname} -> {xname}')
