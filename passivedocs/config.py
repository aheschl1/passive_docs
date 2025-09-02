from pathlib import Path
import yaml

class Config:
    def __init__(self, path: Path):
        self.path = path
        self.data = self.load_config()
        self.__dict__.update(self.data)

    def load_config(self):
        with open(self.path, 'r') as f:
            return yaml.safe_load(f)
