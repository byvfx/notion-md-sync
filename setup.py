from setuptools import setup, find_packages

setup(
    name="notion-md-sync",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "notion-client>=1.0.0",
        "watchdog>=3.0.0",
        "markdown>=3.4.3",
        "python-frontmatter>=1.0.0",
        "click>=8.1.3",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "notion-md-sync=notion_md_sync.cli:main",
        ],
    },
    python_requires=">=3.9",
)