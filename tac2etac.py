import argparse
import json
import copy
from ssagen import crude_ssagen, dse, optimize
from tac import Proc, load_tac
from intergraph import InterGraph
from cfg import infer, linearize

def regalloc(proc, cfg, coalesce = True):
    intergraph = InterGraph(proc, cfg)
    intergraph.greedy_coloring()
    stacksize, alloc = intergraph.get_allocation_record()
    if coalesce:
        intergraph.register_coalesce()
        linearize(proc, intergraph.cfg)
    proc.stacksize = stacksize
    proc.alloc = alloc

def compute_SSA(proc):
    cfg = infer(proc)
    crude_ssagen(proc, cfg)
    dse(cfg)
    optimize(cfg)

    cfg2 = copy.deepcopy(cfg)
    linearize(proc, cfg2)
    return cfg

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Accepts a TAC file and produces ETAC with allocation records"
    )
    argparser.add_argument("source_path", help="path to TAC file in JSON or text", type=str)
    argparser.add_argument(
        "-o",
        help="Allows to specify output file name for the optimized TAC",
    )
    argparser.add_argument('--print', help="Print the produced etac to standard output", action='store_true')
    argparser.add_argument("--no-coalescing", help="Turns off register coalescing", action="store_false")

    args = argparser.parse_args()
    source_path = args.source_path
    output_path = args.o
    print_ = args.print
    coalesce = args.no_coalescing

    if not source_path.endswith('.tac.json'):
        raise ValueError(f'{source_path} not a .tac.json file')

    tac_decls = load_tac(source_path)
    for decl in tac_decls:
        if isinstance(decl, Proc):
            cfg = compute_SSA(decl)
            regalloc(decl, cfg, coalesce)

    etac = [decl.js_obj for decl in tac_decls]

    if print_:
        print(json.dumps(etac, indent=2))

    if not output_path:
        rname = source_path[:-9] + '.etac.json'
        with open(rname, "w") as f:
            f.write(json.dumps(etac, indent=2))
    else:
        with open(output_path, "w") as f:
            f.write(json.dumps(etac, indent=2))