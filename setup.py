from setuptools import setup, find_packages

setup(
    name="passivedocs",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "ollama",
        "python-dotenv",
        "click"
    ],
    entry_points={
        "console_scripts": [
            "passivedocs=main:main"
        ]
    },
    author="",
    description="PassiveDocs project",
    python_requires=">=3.7",
)
