from dataclasses import dataclass, field
from pathlib import Path
import os

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class Settings:
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    model: str = "claude-sonnet-4-5-20250929"
    db_path: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "tutor.db")
    prompts_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "prompts")
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
