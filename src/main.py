#!/usr/bin/python3

import sys
from program import *
import structure

def drop0x(hex: str) -> str:
    return (None if hex is None else
            hex[2:] if hex[0:2] == "0x" else
            hex
           )

def main() -> None:
    for idx, line in enumerate(sys.stdin):
        print(f"{idx}",file = sys.stderr)
        row = line.rstrip('\n').split(',')
        codeid = row[0]
        if codeid == 'codeid':
            continue
        address = row[1]
        code = bytes.fromhex(drop0x(row[2]))
        prog = Program(code)

        prog.pretty_print()

if __name__ == '__main__':
    main()