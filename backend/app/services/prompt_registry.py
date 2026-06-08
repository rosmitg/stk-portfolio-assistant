import yaml
from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"


@lru_cache(maxsize=None)
def load_prompt(name: str) -> dict:
    path = _PROMPTS_DIR / f"{name}.yaml"
    with open(path) as f:
        return yaml.safe_load(f)
