import sys
from pathlib import Path
import click
import os

def system_prompt(readme: str, config: str, repo_root: Path) -> str:
    return """
Your task is to document well
"""

def prepare_context(repo_path: Path):
    config = repo_path / "passivedocs.yml"
    readme = repo_path / "README.md"
    if not config.exists():
        raise FileNotFoundError(f"Expected config file not found: {config}")
    
    return config

def clone_repo(repo_name: str, work_dir: Path):
    os.system(f"git clone {repo_name} {work_dir}/{repo_name.split('/')[-1].replace('.git', '')}")

@click.command()
@click.argument("repo_name")
@click.argument("work_dir", default="./work", type=click.Path())
def main(repo_name, work_dir):
    if not Path(work_dir).exists():
        os.makedirs(work_dir)
        
    clone_repo(repo_name, Path(work_dir))


if __name__ == "__main__":
    main()
