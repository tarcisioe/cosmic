cosmic
======

This is an implementation of the exercises from [Cosmic Python](https://www.cosmicpython.com/).

Commits are tagged according to where in the book the implementation is.

Developing
----------

### Environment
To create a development environment, run

```
poetry install
```

and then activate it with

```
poetry shell
```

Then run

```
pre-commit install
```

to install pre-commit hooks.

### Testing

To run all tests, run

```
summon test
```

for coverage, and optionally html report generation, run

```
summon test --coverage --html
```

### Linting and formatting

To run all linters/static checkers (flake8, pylint, mypy), run

```
summon lint
```

To format code run

```
summon format
```

To just check formatting, run

```
summon format --check
```
