from __future__ import annotations

import argparse
import cmd
import inspect
import sys
import typing as ty

from . import builder, constants, utils

ArgparseShell_T = ty.TypeVar("ArgparseShell_T", bound="ArgparseShell")  # pylint: disable=invalid-name
Namespace = ty.Dict[str, ty.Callable]


class ArgparseShell:
    """
    Argparse shell to combine the functionality of the :py:module:`argparse` and the :py:module:`cmd` module.
    """

    def __init__(self, parser: argparse.ArgumentParser, interactive: cmd.Cmd):
        self.parser = parser
        self.interactive = interactive

    @classmethod
    def from_object(
        cls: ty.Type[ArgparseShell_T],
        program_name: str,
        obj: ty.Any,
        intro: str = None,
    ) -> ArgparseShell_T:
        """
        Factory method to create a ArgparseShell from an arbitrary object.
        The method takes the namespace of the arbitrary object and transforms it to a command line interface.

        See the usage:

        .. code-block:: python

           class Driver:
               def something(self):
                   \"""Do something\"""
                   print("something")

               def something_else(self, value):
                   \"""Do something else\"""
                   print("something_else", value)

           if __name__ == "__main__":
               drv = Driver()
               ArgparseShell.from_object("mycli", drv, intro="Welcome!).main()

        These contents of a file will allow two different things to happen, the file now implements
        a command line interface with the functions defined by the class `Driver` added as commands,
        additionally the file also implements an interactive shell with the driver functions as valid commands.
        The interactive shell is started if the command line interface cannot parse commands.

        Running the interactive shell:

        .. code-block:: shell

           $ ./test/mycli.py
           Welcome!
           mycli>

        Running the command line interface:

        .. code-block:: shell

           $ ./test/mycli.py --help
           usage: mycli [-h] {something,something-else} ...

           positional arguments:
             {something,something-else}  sub-command help
               something        Do something
               foo_default      Do something else

           optional arguments:
             -h, --help         show this help message and exit

        :param cls: Class to create
        :type cls: ty.Type[ArgparseShell_T]
        :param program_name: Name of the program for argparse, as well as the command line prompt
        :type program_name: str
        :param obj: Object to use as base
        :type obj: ty.Any
        :param parent_parsers: Any parent argument parsers to include, defaults to None
        :type parent_parsers: ty.Sequence[argparse.ArgumentParser], optional
        :param intro: Welcome message to print after entering interactive mode, defaults to None
        :type intro: str, optional
        :return: Instance of the ArgparseShell
        :rtype: ArgparseShell_T
        """
        namespace = builder.build_namespace_from_object(obj)
        parser = builder.build_arg_parser_from_namespace(namespace, program_name=program_name)
        interactive = builder.build_interactive_shell_from_namespace(namespace, prompt=f"{program_name}> ", intro=intro)
        return cls(parser, interactive)

    def main(self, argv: ty.Sequence[str] = None):
        """Run the arg shell. The shell first tries to parse"""
        namespace, _ = self.parser.parse_known_args(argv)

        if constants.ARGPARSE_CALLBACK_FUNCTION_NAME in namespace:
            func = getattr(namespace, constants.ARGPARSE_CALLBACK_FUNCTION_NAME)
            self._execute_cli_callback(func, namespace)
        else:
            self._execute_interactive()

    def _execute_interactive(self):
        """Execute the interactive shell"""
        try:
            self.interactive.cmdloop()
        except KeyboardInterrupt:
            self._error("\nAborted!")

    def _execute_cli_callback(self, func: ty.Callable, namespace: argparse.Namespace):
        args, kwargs = utils.parse_arg_string(" ".join(namespace.args))
        try:
            inspect.signature(func).bind(*args, **kwargs)
        except TypeError as exc:
            self.parser.error(str(exc))
        else:
            func(*args, **kwargs)

    def _error(self, msg: str):  # pylint: disable=no-self-use
        """Print the error message and exit with an error code

        :param msg: Exit message to print
        :type msg: str
        """
        print(msg, file=sys.stderr)
        sys.exit(1)
