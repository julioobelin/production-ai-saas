from pathlib import Path

from app.db.vector_schema import SCHEMA_VECTOR_DIMENSIONS

_ALLOWED = {
    Path("app/db/vector_schema.py").as_posix(),
    Path("README.md").as_posix(),
}
_SKIP = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".toml", ".ini", ".sql", ".example"}


def test_schema_width_is_not_hardcoded_outside_persistence() -> None:
    needle = str(SCHEMA_VECTOR_DIMENSIONS)
    offenders: list[str] = []
    for path in Path(".").rglob("*"):
        if not path.is_file():
            continue
        if _SKIP.intersection(path.parts):
            continue
        if path.suffix not in _SUFFIXES and path.name != ".env.example":
            continue
        if needle in path.read_text(encoding="utf-8") and path.as_posix() not in _ALLOWED:
            offenders.append(path.as_posix())
    assert offenders == []
