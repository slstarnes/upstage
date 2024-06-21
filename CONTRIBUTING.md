# Contribution Guide

If you wish to contribute to UPSTAGE, we ask that you follow these steps to ensure code quality.

## Prerequisites

First, get Python 3.11 or 3.12 through your preferred means (conda, mamba, venv, e.g.). We prefer [Mambaforge](https://github.com/conda-forge/miniforge).

> When installing `mambaforge` on Windows, try to install it on `C:\mf`.
This will minimize the path length to avoid issues with the Windows
maximum path restriction. You may need to create the folder first if you
do not have administrator permissions.

Ensure that the pip version is >= `21.3` to allow editable installations with just `pyproject.toml` and the `flit` backend.

```bash
python -m pip install --upgrade pip
```

## Get Started

Clone the repo locally, then install to your environment with:

``pip install -e .[docs,test]``

## Code Quality

Code quality is enforced using these steps:

1. pyproject.toml format (only if you are modifying dependencies, e.g.)
2. SSort
3. Ruff
4. mypy

```bash
pyproject-fmt .\pyproject.toml
ssort .\src\
ruff format .\src\
mypy --show-error-codes -p upstage
```

### Testing

To run the unit tests in `src/upstage/test`, run:

```bash
pytest
```

from the top level of the repo.

Test reports will be in `.\build\reports`

### Building the documentation

Documentation is built from autodocs first, then the source build.

From the top level of the repo:

```bash
sphinx-apidoc -o .\docs\source\ .\src\upstage\ .\src\upstage\test\
sphinx-build -b html .\docs\source .\build\docs
```

Then the docs can be loaded from `.\build\docs\index.html`

## Making Merge Requests

The valid target for all merge requests is `dev`. Please ensure that your merge request includes documentation and explanation for its purpose and sufficient documentation to explain its usage.
