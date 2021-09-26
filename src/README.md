# ETHERseg

## Dependencies

```
pip install cbor2
```

## Usage

```python
import etherseg

etherseg.EtherSeg(code).get_blocks()
```

code has to be a `bytes` containing the code in binary representation

EtherSeg::get_blocks will return a list of tupels representing a block (start, end, type, base)