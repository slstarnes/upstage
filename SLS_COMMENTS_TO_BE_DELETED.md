# Comments from L. Starnes

> Delete this file before merge.

1. It is "UPSTAGE" 122 times over 35 files. 1. In CONTRIBUTING.md you say "then install to your environment with `pip install -e ...`. You had them get mambaforge, but they never set up a conda environment. So, what environment are they installing into? Also, there is no environment.yml -- so does  the `mambaforge` stuff need to be removed? 
1. It looks like you pulled out all the `doit` stuff. I am happy either way -- I did want to make sure that you didn't think that the `doit` powered automation was incompatible in some way with OSS. IMO, as long as it works and is sufficiently documented then its all good. I'm not saying you need to add it back -- it is your call.
1. If `doit` is dead then pull out the `doit` stuff in `pyproject.toml`.
1. You may want to check out poetry. It works on your `pyproject.toml`. It automatically handles creating a lock file (that you put in source control). So instead of `pip install -e`, you would just do `poetry install`. You can install poetry with `curl -sSL https://install.python-poetry.org | python`.
1. The Style Guide says you use Flake 8. You kind of do since the rules are in Ruff, but I would clarify that.
1. In `STYLE_GUIDE.md`, I made a new section called `Linting` which was the first bit of the `Testing` section. I left the words the same but its all about flake8 but are not on the ruff train.
1. In `STYLE_GUIDE.md`, you say
    > Docstring example code tests are executed using [doctest](https://docs.python.org/3/library/doctest.html).

    But, you are not using `doctest`. It does look like there is some test code in your doc strings so maybe you should be?
1. Note how [RMT](https://github.com/gtri/rapid-modeling-tools/blob/master/LICENSE) says the license when you view the LICENSE? [Yours](https://github.com/JamesArruda/upstage/blob/main/LICENSE) does not. Can you try and make that work?
1. It might be worth breaking out a separate `optional-dependencies` for linters/formatters (and not combining with pytest in `test`)
1. In `.github/workflows/lint.yml`, the line `if: success() || failure()` needs tto be removed before merge. Debug only.
1. 