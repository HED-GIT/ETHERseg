from __future__ import annotations

from opcodes import *
import enum
import GLOBALS
from typing import List, Dict

class BlockType(enum.Enum):
    CODE="code"
    META="meta"
    DATA="data"

    def __str__(self) -> str:
        return f"\"{self.value}\""

    def __repr__(self) -> str:
        return str(self)

class Block:

    def __setup(self: Block, code:bytes) -> None:
        skip = 0

        current = 0

        for i in range(self.start,self.end):
            if skip > 0:
                skip -= 1
                continue
            op = all_opcode_by_value(code[i])
            skip = op.push_len()
            self.ins.append((op,i, int.from_bytes(code[i+1:i+skip+1],"big")))

            current += op.pop
            self.needed_stack_size = max(self.needed_stack_size,current)
            current -= op.push
            
    def __is_known(self, stack:[int]) -> bool:
        return stack[-self.needed_stack_size:] in self.known_stack

    def __init__(self, btype:BlockType, start: int, end: int, code:bytes, base: int = 0):
        self.base = base
        self.btype = btype
        self.known_stack: List[List[int]] = []
        self.start = start
        self.end = end
        self.needed_stack_size = 0
        self.ins = []
        self.remaining_calls = GLOBALS.MAX_SINGLE_BLOCK_EXECUTION_SIZE

        # executed and used_in are not garantied to be the same
        # if program-sanitation adds a block only used_in is set
        # currently the sanitation is disabled
        self.executed = False
        self.used_in = None

        self.__setup(code)

    def min_stack_size(self) -> int:
        min_v:int = 0
        cur:int = 0
        for i in self.ins:
            cur -= i[0].pop
            min_v = min(min_v, cur)
            cur += i[0].push

        return min_v * -1 if min_v < 0 else 0

    def execute(self, stack:List[int], jump_dests: List[int]) -> [int]:
        self.used_in = self.base

        if self.remaining_calls == 0:   # == is on purpose to make it run infinitely when MAX_SINGLE_BLOCK_EXECUTION_SIZE is set to negative
            return []
        
        self.remaining_calls-=1

        if self.__is_known(stack):
            return []
        self.known_stack.append(stack[-self.needed_stack_size:])
        ret = []

        for i in self.ins:
            ret = i[0].execute(stack,jump_dests,i[2],i[1])
            if -1 in ret:
                raise Exception("invalid jump dest")
        self.executed = True
        return ret

    def is_reachable(self, all_blocks: Dict[int, Block]) -> bool:

        if hasattr(self,'reachable'):
            return self.reachable
        elif self.was_executed():
            self.reachable = True
            return True
        elif self.ins[0][0] == JUMPDEST:
            self.reachable = True
            return True

        l = [all_blocks[x] for x in all_blocks if x < self.start]
        # true if first block of code
        if len(l) == 0:
            self.reachable = True
            return True

        pre = l[-1]


        if pre.btype != BlockType.CODE:
            self.reachable = False
            return False
        elif pre.ins[-1][0].halts() or pre.ins[-1][0] == JUMP:
            self.reachable = False
            return False
        elif pre.executed:
            self.reachable = True
            return True
        else:
            self.reachable = pre.is_reachable(all_blocks)
            return self.reachable

    def most_likely_code(self, all_blocks: Dict[int, Block]) -> bool:
        if not self.is_reachable(all_blocks):
            return False

        if self.ins[-1][0].is_missing():
            return False

        if self.ins[-1][0].alters_flow() and self.ins[-1][0] != JUMPI:
            return True

        l = [all_blocks[x] for x in all_blocks if x > self.start]

        if len(l) == 0:
            return True

        return l[0].most_likely_code(all_blocks)

    def was_executed(self) -> bool:
        return self.executed
    
    def __lt__(self, value) -> bool:
        if (self.start + self.base) == (value.start + value.base):
            return (self.end + self.base) < (value.end + value.base)
        return (self.start + self.base) < (value.start + value.base)

    def true_end(self) -> int:
        return self.end + self.base
    
    def true_start(self) -> int:
        return self.start + self.base