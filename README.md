# argparse-shell

Interactive shells using argparse

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
