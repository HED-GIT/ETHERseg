# ETHERset

## Dependencies

```
pip install cbor2
```

## Usage

```python
import program

program.Program(code).get_blocks()
```

code has to be a `bytes` containing the code in binary representation

Program::get_blocks will return a list of tupels representing a block (start, end, type, base)