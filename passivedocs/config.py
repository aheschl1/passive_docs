from pathlib import Path
import yaml
from typing import Any, Dict


class Config:
    """Simple config wrapper. If the config file is missing, treat as empty config.

    The object exposes `data` dict and also maps keys to attributes.
    """

    def __init__(self, path: Path | None):
        self.path = path
        self.data: Dict[str, Any] = self.load_config()
        # Map keys to attributes for convenience
        if isinstance(self.data, dict):
            self.__dict__.update(self.data)

    def load_config(self) -> Dict[str, Any]:
        if not self.path or not Path(self.path).exists():
            return {}
        with open(self.path, 'r') as f:
            content = yaml.safe_load(f)
            return content or {}
