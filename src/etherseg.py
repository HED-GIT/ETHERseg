from __future__ import annotations

from block import BlockType, Block
from opcodes import *
import structure
from subprogram import *
from typing import List,Tuple

class EtherSeg:

    def get_blocks(self: EtherSeg) -> List[Tuple[int,int,BlockType,int]]:
        ret = 0
        blocks = []

        if len(self.sub_programs) == 0:
            return

        for i in self.sub_programs:

            code_blocks = [i.blocks[x] for x in i.blocks if i.blocks[x].btype == BlockType.CODE and i.blocks[x].used_in != None]
            if len(code_blocks) == 0:
                return []

            current = code_blocks[0]
            start = code_blocks[0]

            for j in code_blocks[:-1]:

                if current == j:
                    continue
                elif current.true_end() == j.true_start() and current.btype == j.btype:
                    current = j
                elif current.true_end() < j.true_start():
                    blocks.append((start.true_start(),current.true_end(),start.btype,i.base))
                    blocks.append((current.true_end(),j.true_start(),BlockType.DATA,None))
                    start = current = j
                elif current.true_end() == j.true_start() and current.btype != j.btype:
                    blocks.append((start.true_start(),current.true_end(),start.btype,i.base))
                    start = current = j
            blocks.append((start.true_start(),code_blocks[-1].true_end(),start.btype,i.base))

        for i in self.meta:
            blocks.append((i[0],i[1],BlockType.META,None))
        blocks.sort()

        ret_blocks = []
        ret_blocks.append((blocks[0][0],blocks[0][1]-1,blocks[0][2],blocks[0][3]))
        last = blocks[0]
        for i in blocks[1:]:
            if last[0] <= i[0] < last[1]:
                #print("warning overlapping codeblocks")
                pass
            if last[1] < i[0]:
                ret_blocks.append((last[1],i[0]-1,BlockType.DATA,None))
            last = i
            ret_blocks.append((i[0],i[1]-1,i[2],i[3]))
        
        if last[1] < len(self.code):
            ret_blocks.append((last[1],len(self.code),BlockType.DATA,None))
        return ret_blocks

    def pretty_print(self: EtherSeg) -> None:
        b = self.get_blocks()
        if len(b) == 0:
            print(f"{hex(0)},{hex(len(self.code))},{BlockType.DATA},{None}")
            return
        for i in b:
            print(f"{hex(i[0])},{hex(i[1])},{i[2]},{hex(i[3]) if i[3] != None else None}")
  
    def legacy_print(self: Program) -> None:
        b = self.get_blocks()
        if len(b) == 0:
            print(f"{hex(0)},{hex(len(self.code))},{BlockType.DATA}")
            return
        for i in b:
            print(f"{hex(i[0])},{hex(i[1])},{i[2]}")

    def __in_block(self: EtherSeg, block_start: (int,int,BlockType)) -> bool:
        for s in self.sub_programs:
            for b in [x for x in s.blocks if s.blocks[x].btype == BlockType.CODE]:
                if s.blocks[b].true_start() <= block_start[0] < s.blocks[b].true_end():
                    return True
        return False
            
    def __init__(self: EtherSeg, code: bytes):
        self.code = code
        self.sub_programs = []
        self.structure = structure.decompose(code)

        code_blocks = [x for x in self.structure if x[2] == BlockType.CODE]
        self.meta = [x for x in self.structure if x[2] == BlockType.META]
        if len(code_blocks) == 0:
            return

        try:
            self.sub_programs.append(SubProgram(code,code_blocks[0],self.meta))
            self.sub_programs[-1].execute()
        except Exception as e:
            print(e)
        for i in code_blocks[1:]:
            if self.__in_block(i):
                continue

            try:
                self.sub_programs.append(SubProgram(code[i[0]:],i,self.meta))
                self.sub_programs[-1].execute()
            except Exception as e:
                print(e)
                continue
            
