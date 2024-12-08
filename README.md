# 🚲 Bluebikes Trips Analysis Dashboard 🚲

Want to know where people travel using Boston's Bluebikes? See which stations are most
popular and where

# Getting Started
## Installing Dependencies and Packages
### With poetry
This project uses [poetry](https://python-poetry.org) for development and dependency management. Poetry can be installed with [`pipx install poetry`], or see [poetry](https://python-poetry.org/docs/) or [pipx](https://github.com/pypa/pipx) documentation for more information.

Poetry manages virtual environments for you, so to install the development environment, including dependencies for testing, run `poetry install --all-extras`. To check that the installation worked successfully, run `poetry run pytest` to run unit tests.


### Without poetry
Instead of using poetry, you can use the virtual environment of your choosing and install with `pip`.
You will need to install the package in developer mode using the `-e` flag.
This will enable you to develop against the pipeline locally.

To use venv as your development environment, you can install the package as follows, then download the data:

```commandline
python -m venv bbenv
source bbenv/bin/activate
pip install -e .[dev,test]
```