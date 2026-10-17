# Requests for Person A

- No new backend changes are requested right now.
- I already applied the Python 3.12 collection fix in `backend/knowledge.py` by adding `from __future__ import annotations` immediately after the module docstring, because the repo would not collect tests otherwise.
- If you change the knowledge base schema or status payload later, please keep the frontend contract in sync.
