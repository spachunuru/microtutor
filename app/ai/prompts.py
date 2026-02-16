from pathlib import Path
from app.config import settings

_cache: dict[str, str] = {}


def load_prompt(name: str) -> str:
    if name not in _cache:
        path = settings.prompts_dir / f"{name}.md"
        _cache[name] = path.read_text()
    return _cache[name]


def format_prompt(name: str, **kwargs) -> str:
    template = load_prompt(name)
    return template.format(**kwargs)
