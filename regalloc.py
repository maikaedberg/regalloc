import argparse
import json
from tac import Proc, load_tac
from intergraph import InterGraph

def regalloc(fname):
    pass

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
        if not isinstance(decl, Proc):
            continue
        regalloc(decl)

    etac = [decl.js_obj for decl in tac_decls]

    if not output_path:
        print(json.dumps(etac, indent=2))
    else:
        with open(output_path, "w") as f:
            f.write(json.dumps(etac, indent=2))