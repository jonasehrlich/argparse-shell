# argparse-shell

Create interactive shell programs from arbitrary objects using the _argparse_ and _cmd_ modules.

![calculator-example-gif](./examples/calculator-example.gif)

## Usage

Use the `ArgparseShell.from_object` factory method to quickly create an interactive command line interface
for an existing class. Afterwards the application can be run using the `ArgparseShell.main` method.
See the following [./examples/calculator.py](./examples/calculator.py) for a simple example:

``` python
#! /usr/bin/env python3
from argparse_shell import ArgparseShell


class Calculator:
    """A simple calculator example"""

    def add(self, a: float, b: float) -> float:
        """Add two numbers

        :param a: First number
        :param b: Second number
        :return: Sum of two numbers
        """
        return a + b

    def div(self, a: float, b: float) -> float:
        """
        Divide numbers

        :param a: First number
        :param b: Second number
        :return: Division of two numbers"""
        return a / b

    def mult(self, a: float, b: float) -> float:
        """Multiply two numbers

        :param a: First number
        :param b: Second number
        :return: Product of two numbers
        """
        return a * b

    def sub(self, a: float, b: float) -> float:
        """Subtract two numbers

        :param a: First number
        :type a: float
        :param b: Second number
        :type b: float
        :return: Subtraction of the two numbers
        :rtype: float
        """
        return a - b


if __name__ == "__main__":
    calc = Calculator()
    shell = ArgparseShell.from_object(calc, "calc")
    shell.main()

```

## Development

Create a virtual environment using

``` bash
uv sync
```

Install the [pre-commit](https://pre-commit.com/) hooks using

``` bash
pre-commit install
```

Now you have an [editable installation](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs),
ready to develop.

### Testing

After installing all the dependencies, run the test suite using

``` bash
uv run pytest
```

The options for _pytest_ are defined in the _setup.cfg_ and include test coverage check.
The coverage currently has a `fail-under` limit of 75 percent. This limit might get increased when more tests get added.

### Linting and Formatting

The Python code in this repository is linted and formatted using [ruff](https://astral.sh/ruff) with a line length
of 120 characters.
