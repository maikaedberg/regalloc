import argparse
import json
import os
from etac2x64 import destruct_ssa
from tac import Proc, load_tac
from tac2etac import compute_SSA, regalloc
from tac2x64 import tac_to_asm

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Accepts a TAC file and produces the corresponding .s and .exe files"
    )
    argparser.add_argument("source_path", help="path to TAC file in JSON or text", type=str)
    argparser.add_argument("--no-exe", help="Turns off the creation of a .exe", action="store_true")

    args = argparser.parse_args()
    source_path = args.source_path
    no_exe = args.no_exe

    tac_decls = load_tac(source_path)
    for decl in tac_decls:
        if isinstance(decl, Proc):
            # SSA computation and minimization
            cfg = compute_SSA(decl)

            # register allocation
            regalloc(decl, cfg)

            # SSA destruction
            destruct_ssa(decl)

    js_obj = [decl.js_obj for decl in tac_decls]

    asm = tac_to_asm(js_obj)

    rname = source_path[:-9]
    xname = rname + '.exe'
    sname = rname + '.s'
    with open(sname, 'w') as afp:
        print(*asm, file=afp, sep='\n')
    if not no_exe:
        os.system(f'gcc -g -o {xname} {sname} bx_runtime.c')