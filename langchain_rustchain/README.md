# LangChain RustChain Tool

Reference implementation for Elyan Labs bounty #3074.

## Install

```bash
pip install langchain-core pydantic requests
```

## Usage

```python
from rustchain_tool import RustChainTool

tool = RustChainTool()
print(tool.invoke({"action": "get_node_health"}))
print(tool.invoke({"action": "check_balance", "wallet_id": "RTC..."}))
print(tool.invoke({"action": "list_bounties", "limit": 5}))
print(tool.invoke({"action": "get_current_epoch"}))
```

The implementation is intentionally read-only: it does not claim bounties, sign messages, expose credentials, or submit transactions.

## Validation

Run:

```bash
python -m py_compile langchain_rustchain/rustchain_tool.py
python langchain_rustchain/example.py
```

The example performs live read-only calls against `https://rustchain.org`.

Bounty: https://github.com/Scottcjn/rustchain-bounties/issues/3074
