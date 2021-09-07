from __future__ import annotations
from opcodes import *
from block import BlockType, Block
import GLOBALS
from typing import List,Tuple

class SubProgram:

    # sanitize codeblocks
    def __sanitize(self: Program) -> None:
        temp = [value for (key, value) in sorted(self.blocks.items())]

        for i in range(1,len(temp)-1):
            if (temp[i].btype == BlockType.META):
                continue

            # add codeblocks that are reachable but are never executed
            elif GLOBALS.SANITIZE_CODE_BLOCKS           \
                and temp[i].btype == BlockType.CODE     \
                and not temp[i].executed                \
                and temp[i-1].was_executed()            \
                and temp[i].is_reachable(self.blocks):

                for j in range(i,len(temp)-1):
                    if temp[j].was_executed():
                        temp[i].used_in = self.base
                        break
                #temp[i].used_in = temp[i-1].used_in
            
            # remove codeblocks that where never executed
            elif temp[i].btype == BlockType.CODE        \
                and temp[i].used_in == None:

                temp[i].btype = BlockType.DATA

    # splits the code into codeblocks
    def __create_blocks(self: SubProgram) -> None:

        blocks = {}
        skip = 0
        in_data = False

        blocks[0] = (BlockType.CODE,[])
        if all_opcode_by_value(self.code[0]).halts():
            return

        for i in range(len(self.code)):

            if skip > 0:
                skip -= 1
                continue

            for m in self.meta:
                if m[0] <= i + self.base < m[1]:
                    blocks[m[0] - self.base] = (BlockType.META,[])
                    skip = m[1] - (i + self.base)
                    break             
            
            if skip > 0:
                skip -= 1
                continue

            op = all_opcode_by_value(self.code[i])
            
            skip = op.push_len() #stuff can still be skipped do to how push in data works

            if in_data:
                if op.is_invalid():
                    continue
                else:
                    blocks[i] = (BlockType.CODE,[]) # now begins code
                    in_data = False
                    continue
            else:
                if op == JUMPDEST:
                    blocks[i] = (BlockType.CODE,[])
                elif op.is_invalid():
                    blocks[i] = (BlockType.DATA,None)
                    in_data = True
                elif op.alters_flow():
                    if i + 2 < len(self.code):
                        blocks[i+1] = (BlockType.DATA,None) if all_opcode_by_value(self.code[i+2]).is_invalid() else (BlockType.CODE,[])
                        in_data = blocks[i+1][0] == BlockType.DATA

        keys = sorted(blocks)
        for i in range(len(keys) - 1):
            self.blocks[keys[i]] = Block(blocks[keys[i]][0],keys[i],keys[i+1],self.code,self.base)
        self.blocks[keys[-1]] = Block(blocks[keys[-1]][0],keys[-1],len(self.code),self.code,self.base)

    def __create_jump_dests(self) -> List[int]:
        skip: int = 0 
        jump_dests = []
        for i in range(0,len(self.code)):
            if skip > 0:    
                skip -= 1
                continue

            skip = self.code[i] - PUSH1.code + 1 if PUSH1.code <= self.code[i] <= PUSH32.code else 0

            if self.code[i] == JUMPDEST.code:
                jump_dests.append(i)
        return jump_dests

    def execute(self:SubProgram) -> None:
        if self.blocks[0].min_stack_size() > 0:
            self.blocks = {0:Block(BlockType.DATA,0,len(self.code),self.code,self.base)}
            return
        self.__execute()
        self.__secondary_execution()
        self.__sanitize()

    def __secondary_execution(self: SubProgram) -> None:
        if GLOBALS.SECONDARY_EXECUTION:
            b = [x for x in self.blocks if self.blocks[x].btype == BlockType.CODE]
            b.sort()

            for i in range(len(b)-1,0,-1):
                if not (self.blocks[b[i]].was_executed() or self.blocks[b[i]].most_likely_code(self.blocks)):
                    del b[i]
                else:
                    break
            for i in b:
                if i + self.base >= self.predicted_end:
                    break
                if not self.blocks[i].was_executed() and self.blocks[i].most_likely_code(self.blocks): 
                    try:
                        self.__execute(i,[None]* GLOBALS.SECONDARY_STACK_SIZE(self.blocks[i].min_stack_size()))
                    except Exception as e:
                        pass
        
    def __execute(self:SubProgram, start: int = 0, stack:List[int] = []) -> None:

        check = [] # holds list of index-stack pairs that have to be checked, (index of codeblock, stack to test that block on)

        if not start in self.blocks and self.blocks[start].btype != BlockType.CODE:
            return 
        
        ret = []
        try:
            ret = self.blocks[start].execute(stack,self.jump_dests)
        except Exception as e:
            pass

        for i in ret:
            check += [(i,stack.copy())]

        check_count = 0

        while(check!=[] and check_count != GLOBALS.MAX_TOTAL_BLOCK_EXECUTION_SIZE):
            check_count += 1
            current = check.pop()
            if not current[0] in self.blocks or self.blocks[current[0]].btype != BlockType.CODE:    
                #ignore if no block exists/ block is not code, can happen for jumpi that act as normal jump
                continue
            try:
                ret = self.blocks[current[0]].execute(current[1],self.jump_dests)
                for i in ret:
                    check.append((i,current[1].copy()))
            except Exception as e:
                pass

    def __init__(self, code:bytes, size: Tuple[int,int,BlockType], meta:List[Tuple[int,int]]):
        self.code = code
        self.base = size[0]
        self.meta = meta
        self.predicted_end = size[1]
        self.blocks: {int,Block} = {}
        self.jump_dests: [int] = self.__create_jump_dests()
        self.__create_blocks()    