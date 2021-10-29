# argparse-shell

Create interactive shell programs from arbitrary objects using the _argparse_ and _cmd_ modules.

## Usage

Use the `ArgparseShell.from_object` factory method to quickly create an interactive command line interface
for an existing class. Afterwards the application can be run using the `ArgparseShell.main` method.
See the following _calc.py_:

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

Run the interactive shell:

``` bash
$ ./calc.py
calc> help

Documented commands (type help <topic>):
========================================
add  div  help  mult  sub
calc> help add
usage: add a b

Add two numbers

Parameters:
  a: float      First number
  b: float      Second number

Returns:
  float: Sum of two numbers

calc> add 40 2
42
```

Run the command line interface:

``` bash
$ ./calc.py --help
usage: calc [-h] {add,div,mult,sub} ...

A simple calculator example

options:
  -h, --help          show this help message and exit

sub commands:
  {add,div,mult,sub}
    add               Add two numbers
    div               Divide numbers
    mult              Multiply two numbers
    sub               Subtract two numbers
$ ./calc.py add --help
usage: calc add [-h] a b

Add two numbers

positional arguments:
  a           First number
  b           Second number

options:
  -h, --help  show this help message and exit
$ ./calc.py add 38 4
42
```

## Development

Fork the repository from [Github](https://github.com/jonasehrlich/argparse-shell)

Clone your version of the repository

``` bash
git clone https://github.com/<your-username>/argparse-shell
```

Install the dependencies and dev dependencies using

``` bash
pip install -e .[dev]
```

Install the [pre-commit](https://pre-commit.com/) hooks using

``` bash
$ pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

Now you have an [editable installation](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs),
ready to develop.

### Testing

After installing all the dependencies, run the test suite using

``` bash
pytest
```

The options for _pytest_ are defined in the _setup.cfg_ and include test coverage check.
The coverage currently has a `fail-under` limit of 75 percent. This limit might get increased when more tests get added.

### Formatting

The Python code in this repository is formatted using black [black](https://github.com/psf/black) with a line length
of 120 characters. The configuration for _black_ is located in the section `[tool.black]` section of _pyproject.toml_.

### Linting

Linting is implemented using [flake8](https://github.com/PyCQA/flake8). The configuration for _flake8_ is located in
the section `[flake8]` of the _setup.cfg_.
