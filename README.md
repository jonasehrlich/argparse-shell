# argparse-shell

Create interactive shell programs from arbitrary objects using the _argparse_ and _cmd_ modules.

## Usage

Use the `ArgparseShell.from_object` factory method to quickly create an interactive command line interface
for an existing class.

``` python
from argparse_shell import ArgparseShell

class MyDriver:
    def foo(self, bar: int):
        """Do foo"""
        print("running foo, bar:", bar)
        return bar

    def foo_default(self, bar: int = 123):
        """Do something else"""
        print("running foo-default, bar:", bar)
        return bar


if __name__ == "__main__":
    drv = MyDriver()
    shell = ArgparseShell.from_object("mycli", drv, intro="Welcome to mycli!")
    shell.main()

```

Running the interactive shell:

``` bash
$ ./test/mycli.py
Welcome!
mycli>
```

Running the command line interface:

``` bash

$ ./test/mycli.py --help
usage: mycli [-h] {something,something-else} ...

positional arguments:
  {foo,foo-default}  sub-command help
    foo              Do foo
    foo_default      Do something else

optional arguments:
  -h, --help         show this help message and exit
```

## Development

Fork the repository from [Github](https://github.com/jonasehrlich/argparse-shell)

Clone your version of the repository

``` bash
$ git clone https://github.com/<your-username>/argparse-shell
```

Install the dependencies and dev dependencies using

``` bash
$ pip install -e .[dev]
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
