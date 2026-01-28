# Fixes Applied

## Import Path Update (2025-01-27)

**Issue:** `ModuleNotFoundError: No module named 'langchain.schema'`

**Root Cause:** LangChain reorganized imports in v0.3+. The `langchain.schema` module was moved to `langchain_core.messages`.

**Fix Applied:**
- Updated all workflow files to use `from langchain_core.messages import HumanMessage, SystemMessage`
- Added `langchain-core>=0.3.0` to dependencies in `pyproject.toml`

**Files Modified:**
- `src/amber/workflows/on_demand.py`
- `src/amber/workflows/background.py`
- `src/amber/workflows/scheduled.py`
- `src/amber/workflows/webhook.py`
- `pyproject.toml`

## Python Version Constraint (2025-01-27)

**Issue:** Pydantic v1 compatibility warning with Python 3.14

**Root Cause:** LangChain dependencies use Pydantic v1 which isn't fully compatible with Python 3.14+

**Fix Applied:**
- Added Python version constraint: `requires-python = ">=3.11,<3.14"`
- This ensures installation on Python 3.11, 3.12, or 3.13

**Files Modified:**
- `pyproject.toml`

## Testing After Fixes

```bash
# Reinstall dependencies
pip install -e .

# Test service starts without errors
python -m amber.service
```

Expected output:
```
{"event": "Starting Amber LangGraph service", ...}
{"event": "PostgreSQL checkpointer initialized", ...}
{"event": "Supervisor graph compiled", ...}
```

Service should start on http://localhost:8000
