from setuptools import setup, find_packages

setup(
    name="passivedocs",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "ollama",
        "python-dotenv",
        "click",
        "PyYAML",
        # 'glob' is part of the stdlib; not a real dependency
    ],
    entry_points={
        "console_scripts": [
            "passivedocs=passivedocs.main:main"
        ]
    },
    author="",
    description="PassiveDocs project",
    python_requires=">=3.7",
)
