from fnmatch import fnmatch
from pathlib import Path
import click
import os
import glob
import logging
import sys

from .agent import DocAgent
from .config import Config


def prepare_context(repo_path: Path):
    config = repo_path / "passivedocs.yml"
    readme = repo_path / "README.md"
    if not config.exists():
        raise FileNotFoundError(f"Expected config file not found: {config}")
    
    with open(readme, 'r') as f:
        readme = f.read()

    config = Config(config)

    return readme, config


def clone_repo(repo_name: str, work_dir: Path):
    os.makedirs(work_dir, exist_ok=True)
    # remove the repo if exists
    if (work_dir / repo_name.split('/')[-1].replace('.git', '')).exists():
        os.system(f"rm -rf {work_dir}/{repo_name.split('/')[-1].replace('.git', '')}")
    os.system(f"git clone {repo_name} {work_dir}/{repo_name.split('/')[-1].replace('.git', '')}")
    return Path(work_dir) / repo_name.split('/')[-1].replace('.git', '')


def get_target_files(repo_dir: Path, config: Config):
    files = glob.glob(str(repo_dir / '**' / '*'), recursive=True)
    # config has .ignore which holds regex patterns
    ignored_files = config.data.get('ignore', [])
    for pattern in ignored_files:
        files = [f for f in files if not fnmatch(f, pattern)]
    files = [f for f in files if Path(f).is_file()]
    return files


def setup_logging(log_file: str | None, level: str) -> None:
    """Configure logging to stdout and optionally to a file."""
    root = logging.getLogger()
    # clear existing handlers
    for h in list(root.handlers):
        root.removeHandler(h)

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(numeric_level)

    # Stream to stdout
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(numeric_level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    sh.setFormatter(fmt)
    root.addHandler(sh)

    # Optional file handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(numeric_level)
        fh.setFormatter(fmt)
        root.addHandler(fh)

def make_pr(repo_dir: Path):
    os.system(f"cd {repo_dir} && git checkout -b docs")
    os.system(f"cd {repo_dir} && git add .")
    os.system(f"cd {repo_dir} && git commit -m 'Update documentation'")
    os.system(f"cd {repo_dir} && git push origin docs")


@click.command()
@click.option("--log-file", default=None, type=click.Path(), help="Optional path to write logs to.")
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=True),
    help="Logging level",
)
@click.argument("repo_name")
@click.argument("work_dir", default="./work", type=click.Path())
def main(repo_name, work_dir, log_file, log_level):
    setup_logging(log_file, log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting passivedocs for repo: %s", repo_name)

    if not Path(work_dir).exists():
        logger.debug("Creating work_dir: %s", work_dir)
        os.makedirs(work_dir)
        
    repo_dir = clone_repo(repo_name, Path(work_dir))
    logger.info("Cloned repository to %s", repo_dir)

    readme, config = prepare_context(repo_dir)
    logger.debug("Loaded config and readme; looking for target files")

    files = get_target_files(repo_dir, config)
    logger.info("Found %d target files to consider", len(files))

    agent = DocAgent(readme=readme, files=files)
    logger.info("Initialized DocAgent; beginning iteration")

    agent.iterate()
    logger.info("passivedocs run complete")

    make_pr(repo_dir)


if __name__ == "__main__":
    main()
