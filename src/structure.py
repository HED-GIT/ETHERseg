import io,re,cbor2
import opcodes
from block import *

PUSHPOP = b'(\x60.|\x61..|\x62...|\x63.{4}|\x64.{5}|\x65.{6}|\x66.{7}|\x67.{8}|\x68.{9}|\x69.{10}|\x6a.{11}|\x6b.{12}|\x6c.{13}|\x6d.{14}|\x6e.{15}|\x6f.{16}|\x70.{17}|\x71.{18}|\x72.{19}|\x73.{20}|\x74.{21}|\x75.{22}|\x76.{23}|\x77.{24}|\x78.{25}|\x79.{26}|\x7a.{27}|\\\x7b.{28}|\\\x7c.{29}|\\\x7d.{30}|\x7e.{31}|\x7f.{32})\x50'
CONTRACT_OLD = b'\x60\x60\x60\x40(\x81\x90|\x90\x81)?\x52'
CONTRACT_NEW = b'\x60\x80\x60\x40(\x81\x90|\x90\x81)?\x52'
CONTRACT_NEW2 = b'(?<=\x56[\x00\xfe])\x60.\x60\x40'
LIBRARY_CHECK  = b'\x73.{20}\x30\x14'
SOLIDITY_START = b'(' + PUSHPOP + b'|' + LIBRARY_CHECK + b')?(' + CONTRACT_OLD + b'|' + CONTRACT_NEW + b')' + b'|' + CONTRACT_NEW2

# DUP1 PUSH1 . PUSH1 00 CODECOPY PUSH1 00 RETURN STOP (PUSH1 00 CALLDATALOAD | CALLDATASIZE)
DEPLOYMENT1 = b'(?<=\x80\x60.\x60\x00\x39\x60\x00\xf3\x00)(\x60\x00\x35|\x36)'
# DUP1 PUSH2 .. PUSH1 00 CODECOPY PUSH1 00 RETURN STOP (PUSH1 00 CALLDATALOAD | CALLDATASIZE)
DEPLOYMENT2 = b'(?<=\x80\x61..\x60\x00\x39\x60\x00\xf3\x00)(\x60\x00\x35|\xe6)'
# DUP1 PUSH2 .. PUSH1 00 CODECOPY PUSH2 .. JUMP PUSH1 00 PUSH2 .. MSTORE8
DEPLOYMENT3 = b'(?<=\x80\x61..\x60\x00\x39\x61..\x56)\x60\x00\x61..\x53'
# JUMP PUSH1 00 DATALOAD
DEPLOYMENT4 = b'(?<=\x56)\x60\x00\x35'
# DUP1 PUSH1 . PUSH1 00 CODECOPY PUSH1 00 RETURN PUSH1 
DEPLOYMENT5 = b'(?<=\x80\x60.\x60\x00\x39\x60\x00\xf3)\x60'

RE_CODE_START = re.compile(SOLIDITY_START + b'|' + DEPLOYMENT1 + b'|' + DEPLOYMENT2 + b'|' + DEPLOYMENT3 + b'|' + DEPLOYMENT4 + b'|' + DEPLOYMENT5, re.DOTALL)

STOP = b'\x00'
JUMP = b'\x56'
RETURN = b'\xf3'
INVALID = b'\xfe'
SELFDESTRUCT = b'\xff'

BZZR0 = b'bzzr0'
BZZR1 = b'bzzr1'
IPFS  = b'ipfs'
SOURCE_RE = re.compile(BZZR0 + b'|' + BZZR1 + b'|' + IPFS)
METADATA_OFFSET = 50

def matchMetadata(code,keyword):
    try:
        fp = io.BytesIO(code)
        metadata = cbor2.load(fp)
        rest = fp.read()
        len_metadata = int.from_bytes(rest[:2],'big')
        if len(rest) >= 2 and len(code) == len_metadata + len(rest) and keyword.decode('ascii') in metadata:
            return code[:len_metadata+2]
        else:
            return b''
    except:
        return b''

def searchMetadata(code):
    parts = []
    code_start = 0
    i = 0
    while True:
        source_match = SOURCE_RE.search(code,i)
        if source_match is None:
            break
        source_start = source_match.start()
        metadata = b''
        metadata_start = source_start
        for j in range(source_start-2,max(source_start-METADATA_OFFSET,0)-1,-1):
            metadata = matchMetadata(code[j:],source_match[0])
            if metadata != b'':
                metadata_start = j
                break
        metadata_end = metadata_start + len(metadata) 
        if metadata_end > source_start:
            if metadata_start > code_start:
                parts.append((code_start,metadata_start - 1,BlockType.CODE))
            parts.append((metadata_start,metadata_end,BlockType.META))
            code_start = metadata_end
            i = metadata_end
        else:
            i = source_start + 1
    if code_start < len(code):
        parts.append((code_start,len(code),BlockType.CODE))
    return parts

def splitCode(code,block):
    i = block[0]
    parts = []
    for m in RE_CODE_START.finditer(code[block[0]:block[1]]):
        parts.append((i,block[0] + m.start()))
        i = block[0] + m.start()
    if i < block[1]:
        parts.append((i,block[1]))
    return parts

def decompose(code):
    parts = []
    preMeta = True
    for p in searchMetadata(code):
        if p[2] == BlockType.META:
            parts.append(p)
            preMeta = False
        else:
            pc_parts = splitCode(code,p)
            if len(pc_parts) > 0:
                if pc_parts[0][0] != pc_parts[0][1]:
                    if preMeta:
                        pass
                        parts.append((pc_parts[0][0],pc_parts[0][1],BlockType.CODE))
                    else:
                        parts.append((pc_parts[0][0],pc_parts[0][1],BlockType.DATA))
                parts.extend([(c[0],c[1],BlockType.CODE) for c in pc_parts[1:]])
    
    return parts