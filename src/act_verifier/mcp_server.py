"""MCP-сервер, щоб Claude Code / Claude Desktop викликав верифікатор як інструмент.

Етап 2, після того як CLI і тести зелені. Ідея інструментів:
  - verify_act(contract_path, previous_paths, act_path) -> вердикт + знахідки + блок доказів
  - list_checks() -> каталог перевірок з docs/checks.md

Агент готує, людина вирішує: сервер лише читає файли і нічого не змінює в них.
Бібліотека: пакет `mcp` (FastMCP), див. extras `mcp` у pyproject.toml.
"""
