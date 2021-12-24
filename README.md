# Regalloc CSE302 Project

In this project we have implemented register allocation for TAC to generate efficient x64 by using multiple registers at once.

We have thus implemented the following:
- SSA minimization
    - Null choice elimination (Vishrut)
    - Rename Elimination (Vishrut)
- Register allocation
    - The creation of an interference graph (Maika & Remy)
    - Max Cardinality Search to find a Simplicial Elimination Ordering (Maika & Remy)
    - Greedy coloring of the graph using the SEO (Maika & Remy)
    - Temporary Spilling (Maika & Remy)
- Register Coalescing (Vishrut)
- x64 Generation
    - SSA destruction (Remy)
    - ETAC to x64 compilation using an allocation record (Maika)

## What drivers and how to use them

We provide three drivers to call the implemented features:

#### [tac2etac.py](https://github.com/maikaedberg/regalloc/blob/main/tac2etac.py)
Creates an etac file with an allocation record from a ```.tac.json``` file.
Use:
```
python3 tac2etac.py path/file.tac.json -o path/file.etac.json --print --no-coalescing
```
Where the optional ```-o``` flag can be used to specify an output file, the ```--print``` flag can be used if the produced etac should be displayed and the ```--no-coalescing``` flag can be used to disable register coalescing.

#### [etac2x64.py](https://github.com/maikaedberg/regalloc/blob/main/etac2x64.py)
Creates a source code file and an executable from a ```.etac.json``` file.
Use:
```
python3 etac2x64.py path/file.etac.json --no-exe
```
Where the ```--no-exe``` can be used to disable the generation of an executable.

#### [regalloc.py](https://github.com/maikaedberg/regalloc/blob/main/regalloc.py)
Creates a source code file and an executable from a ```.tac.json``` file. It servers the same purpose as successively using tac2etac and then etac2x64.
Use:
```
python3 regalloc.py path/file.tac.json --no-exe --no-coalescing
```
Where the ```--no-exe``` and ```--no-coalescing``` flag are the same as above.