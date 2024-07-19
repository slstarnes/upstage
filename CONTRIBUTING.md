# Contribution Guide

All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.

## Bug Reports and Enhancement Requests

Bug reports and enhancement requests are an important part of making UPSTAGE more stable and are curated though [Github issues](https://github.com/gtri/upstage/issues). If you wish to contribute, then please be sure there is an active issue to work against and there is not then go ahead and create one.

## Create a Fork

You will need your own copy of UPSTAGE (aka fork) to work on the code. Go to the [UPSTAGE project page](https://github.com/gtri/upstage) and hit the `Fork` button.

## Making Code Changes

If you wish to contribute to UPSTAGE, we ask that you follow these steps to ensure code quality.

### Development Environment Setup

First, get Python 3.11 or 3.12 through your preferred means (conda, mamba, venv, e.g.).
We prefer [Mambaforge](https://github.com/conda-forge/miniforge).

> When installing `mambaforge` on Windows, try to install it on `C:\mf`.
This will minimize the path length to avoid issues with the Windows
maximum path restriction. You may need to create the folder first if you
do not have administrator permissions.

Ensure that the pip version is >= `21.3` to allow editable installations with just `pyproject.toml`
and the `flit` backend.

```bash
python -m pip install --upgrade pip
```

Next, clone the repo locally

```bash
git clone https://github.com/gtri/upstage.git
cd upstage
```

Install UPSTAGE to your environment with

```bash
pip install -e .[docs,test]
```

### Style Guide

For style, see [STYLE_GUIDE](STYLE_GUIDE.md).

### Code Quality

Code quality is enforced using the following tools:

1. [`pyproject-fmt`](https://pyproject-fmt.readthedocs.io/en/latest/) - pyproject.toml formatter
2. [`ssort`](https://pyproject-fmt.readthedocs.io/en/latest/) - source code sorter
3. [`ruff`](https://docs.astral.sh/ruff/) - linter and code formatter
4. [`mypy`](https://mypy-lang.org/) - static type checker

These tools are run as follows:

```bash
# formatters
pyproject-fmt .\pyproject.toml
ssort .\src\
ruff format .\src\
# linters
ruff check --fix .\src\
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

## Making Pull Requests

The valid target for all pull requests is `dev`. Please ensure that your pull request includes
documentation and explanation for its purpose and sufficient documentation to explain its usage.
