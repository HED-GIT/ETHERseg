from typing import Callable,List

"""sets how often a single block gets executed at most, negative means infinite but may lead to infinity loop"""
MAX_SINGLE_BLOCK_EXECUTION_SIZE:int = 100
"""sets how many block executions are called at most, negative means infinite but may lead to infinity loop"""
MAX_TOTAL_BLOCK_EXECUTION_SIZE:int = -1

"""sets which exponent should be calculated"""
MAX_EXPONENT_CAP:bool = True
MAX_EXPONENT_CAP_VALUE: int = 257

"""list of accepted invalid jumpdests"""
KNOWN_INVALID_JUMPDEST: List[int] = [0,2,4,7]

"""sets if possible codeblocks should be executed again"""
SECONDARY_EXECUTION: bool = True
"""function to calculate the given stack size for secondary executions"""
SECONDARY_STACK_SIZE: Callable[[int],int] = lambda n_stack: n_stack * 2
"""sets if reachable but not executed codeblocks should be added"""
SANITIZE_CODE_BLOCKS: bool = False

"""decides if a single invalid inbetween code is considered code or not"""
SINGLE_INVALIDS_ARE_CODE: bool = True