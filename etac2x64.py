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
        correspondences = []
        to = set()
        for instr in phi_l:
            to.add(instr.dest)
            for label, temp in instr.arg1.items():
                correspondences.append((temp, instr.dest, label))
    
        # Eagerly emit a >> b when there is no _ >> a
        for (a, b, label) in correspondences.copy():
            if a not in to:
                correspondences.remove((a, b, label))
                emit(a, b, label, proc)
        
        while len(correspondences) > 1:
            # pick a dummy temporary x
            x = fresh(temp_counter)
            temp_counter += 1

            # emit a >> x
            a, b, label = correspondences[0]
            emit(a, x, label, proc)

            # replace all a >> _ by x >> _
            for (a2, b, label) in correspondences.copy():
                if a2 == a:
                    emit(x, b, label, proc)
                    correspondences.remove((a2, b, label))
        
        if len(correspondences) == 1:
            (a, b, label) = correspondences[0]
            emit(a, b, label, proc)

    # remove phi functions from the instructions
    proc.body = [i for i in proc.body if i.opcode != "phi"]

        
if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Accepts a ETAC file and produces the corresponding .s and .exe files"
    )
    argparser.add_argument("source_path", help="path to ETAC file in JSON or text", type=str)
    argparser.add_argument("--no-exe", help="Turns off the creation of a .exe", action="store_true")

    args = argparser.parse_args()
    source_path = args.source_path
    no_exe = args.no_exe

    if not source_path.endswith('.etac.json'):
        raise ValueError(f'{source_path} not a .etac.json file')

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
    if not no_exe:
        os.system(f'gcc -g -o {xname} {sname} bx_runtime.c')
