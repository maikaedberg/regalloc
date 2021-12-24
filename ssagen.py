#!/usr/bin/env python3

import tac
import cfg as cfglib
import re, random, os
from copy import copy 
# ------------------------------------------------------------------------------
# liveness

_arg1_use = re.compile(r'add|sub|mul|div|mod|neg|and|or|xor|not|shl|shr|copy|ret|jz|jnz|jl|jle|jnl|jnle')
_arg2_use = re.compile(r'add|sub|mul|div|mod|and|or|xor|shl|shr|param')
_dest_def = re.compile(r'add|sub|mul|div|mod|neg|and|or|xor|not|shl|shr|const|copy|phi|call')

def use_set(instr):
    s = set()
    if _arg1_use.fullmatch(instr.opcode) and instr.arg1: s.add(instr.arg1)
    if _arg2_use.fullmatch(instr.opcode) and instr.arg2: s.add(instr.arg2)
    if instr.opcode == 'phi': s.update(instr.arg1.values())
    return s

def rewrite_use_temps_nonphi(instr, fn):
    if _arg1_use.fullmatch(instr.opcode) and instr.arg1:
        instr.arg1 = fn(instr.arg1)
    if _arg2_use.fullmatch(instr.opcode) and instr.arg2:
        instr.arg2 = fn(instr.arg2)

def def_set(instr):
    s = set()
    if _dest_def.fullmatch(instr.opcode) and instr.dest: s.add(instr.dest)
    return s

def rewrite_temps(instr, fn):
    if _arg1_use.fullmatch(instr.opcode) and instr.arg1:
        instr.arg1 = fn(instr.arg1)
    if _arg2_use.fullmatch(instr.opcode) and instr.arg2:
        instr.arg2 = fn(instr.arg2)
    if instr.opcode == 'phi':
        for l, t in instr.arg1.items():
            instr.arg1[l] = fn(t)
    if _dest_def.fullmatch(instr.opcode) and instr.dest:
        instr.dest = fn(instr.dest)

# ------------------------------------------------------------------------------
# crude SSA gen


def tmp_root(tmp):
    try: return tmp[:tmp.rindex('.')]
    except ValueError: return tmp

def tmp_version(tmp):
    try: return tmp[tmp.rindex('.')+1:]
    except ValueError: return ''

def crude_ssagen(tlv, cfg):
    livein, liveout = dict(), dict()
    cfglib.recompute_liveness(cfg, livein, liveout)
    for bl in cfg.nodes():
        prev_labs = list(cfg.predecessors(bl.label))
        ts = livein[bl.first_instr()]
        if bl.label == cfg.lab_entry: prev_labs.append(cfg.proc_name)
        if len(prev_labs) == 0: prev_labs = [cfg.proc_name]
        bl.body[:0] = [tac.Instr(t, 'phi', ({l: t for l in prev_labs}, None)) \
                       for t in ts]
    versions = cfglib.counter(transfn=lambda x: f'.{x}')
    for i in cfg.instrs():
        if i.dest and i.dest.startswith('%'):
            i.dest = i.dest + next(versions)
    ver_maps = {cfg.proc_name: {t: t for t in tlv.t_args}}
    for bl in cfg.nodes():
        ver_map = dict()
        for instr in bl.instrs():
            rewrite_use_temps_nonphi(instr, lambda t: ver_map.get(t, t))
            if instr.dest:
                ver_map[tmp_root(instr.dest)] = instr.dest
        ver_maps[bl.label] = ver_map
    for bl in cfg.nodes():
        for instr in bl.instrs():
            if instr.opcode != 'phi': continue
            for lab_prev, root in instr.arg1.items():
                instr.arg1[lab_prev] = ver_maps[lab_prev].get(root, root)
              
# ------------------------------------------------------------------------------
def replace(cfg, u, v):
    """
    Go over the whole cfg, replacing any instance of the temporary u with v
    """
    for block in cfg.nodes():
        for instr in block.body:
            if instr.dest == u: instr.dest = v
            if instr.opcode == "phi":
                for label, temp in instr.arg1.copy().items():
                    if temp == u:
                        instr.arg1[label] = v
            else:
                if instr.arg1 == u: instr.arg1 = v
                if instr.arg2 == u: instr.arg2 = v


def null_choice(cfg):
    '''remove a phi instr if it is redundent'''
    changed = False
    for block in cfg.nodes():
        for instr in block.body.copy():
            if instr.opcode == "phi":
                if all(temp == instr.dest for temp in instr.arg1.values()):
                    block.body.remove(instr)
                    changed = True
    
    return changed

def reassemble(root, version):
    version = version.strip()
    if version != '':
        return root + '.' + version
    else:
        return root

def rename(cfg):
    '''Remove a rename phi instr'''    
    changed = False
    for block in cfg.nodes():
        for instr in block.body:
            if instr.opcode == "phi":
                root = tmp_root(instr.dest)
                u = tmp_version(instr.dest)
                v = None
                for temp in instr.arg1.values():
                    temp_root = tmp_root(temp)
                    temp_version = tmp_version(temp)
                    if temp_root != root:
                        break
                    if v is None and temp_version != u:
                        v = temp_version
                    elif temp_version != v and temp_version != u:
                        break
                else:
                    if v is not None:
                        full_u = reassemble(root, u)
                        full_v = reassemble(root, v)
                        replace(cfg, full_u, full_v)
                        changed = True
    return changed

def optimize (cfg):
    changed = True
    while changed:
        changed = False
        changed |= rename(cfg)
    
    null_choice(cfg)

# ------------------------------------------------------------------------------
def dse(cfg):
    changed = True
    while changed:
        changed = False
        livein, liveout = dict(), dict()
        cfglib.recompute_liveness(cfg, livein, liveout)

        label_stack, visited = [cfg.lab_entry], []
        while len(label_stack) > 0:
            label = label_stack.pop()
            for instr in cfg[label].instrs():
                if instr.opcode in {"call", "div", "mod"}:
                    continue
                if instr.dest is None:
                    continue
                if instr.dest not in liveout[instr]:
                    cfg[label].body.remove(instr)
                    changed = True
            label_stack += [i for i in cfg.successors(label) if i not in visited]
            visited.append(label)

# ------------------------------------------------------------------------------

def make_dotfiles(cfg, procname, fname, verbosity):
    if fname.endswith('.tac.json'): fname = fname[:-5]
    kwargs = dict()
    if verbosity >= 1:
        livein, liveout = dict(), dict()
        cfglib.recompute_liveness(cfg, livein, liveout)
        kwargs['livein'] = livein
        kwargs['liveout'] = liveout
    cfg.write_dot(fname, **kwargs)
    os.system(f'dot -Tpdf -O {fname}.{procname}.dot')

if __name__ == '__main__':
    import os
    from argparse import ArgumentParser
    ap = ArgumentParser(description='TAC library, parser, and interpreter')
    ap.add_argument('file', metavar='FILE', type=str, nargs=1, help='A TAC file')
    ap.add_argument('-v', dest='verbosity', default=0, action='count',
                    help='increase verbosity')
    args = ap.parse_args()
    gvars, procs = dict(), dict()
    for tlv in tac.load_tac(args.file[0]):
        if isinstance(tlv, tac.Proc):
            cfg = cfglib.infer(tlv)
            crude_ssagen(tlv, cfg)
            make_dotfiles(cfg, tlv.name[1:], args.file[0], args.verbosity)
            if args.verbosity >= 2:
                cfglib.linearize(tlv, cfg)
                print(tlv)
