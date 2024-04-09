from __future__ import annotations

import argparse
import cmd
import collections.abc
import inspect
import sys
import typing as ty

from . import builder, constants
from .namespace import Namespace, UnboundNamespace

if sys.version_info < (3, 11):
    from typing_extensions import Self
else:
    from typing import Self

ArgparseShell_T = ty.TypeVar("ArgparseShell_T", bound="ArgparseShell")  # pylint: disable=invalid-name


class ArgparseShell:
    """
    Argparse shell to combine the functionality of the :py:module:`argparse` and the :py:module:`cmd` module.
    """

    def __init__(self, parser: argparse.ArgumentParser, interactive: cmd.Cmd):
        self.parser = parser
        self.interactive = interactive

    @classmethod
    def from_object(
        cls,
        obj: ty.Any,
        program_name: str,
        intro: ty.Optional[str] = None,
        description: ty.Optional[str] = None,
        nested_namespaces: ty.Optional[collections.abc.Mapping[str, UnboundNamespace]] = None,
        *,
        stdin: ty.Optional[ty.TextIO] = None,
        stdout: ty.Optional[ty.TextIO] = None,
    ) -> Self:
        """
        Factory method to create a ArgparseShell from an arbitrary object.
        The method takes the namespace of the arbitrary object and transforms it to a command line interface.

        :param cls: Class to create
        :type cls: ty.Type[ArgparseShell_T]
        :param obj: Object to use as base
        :type obj: ty.Any
        :param program_name: Name of the program for argparse, as well as the command line prompt
        :type program_name: str
        :param parent_parsers: Any parent argument parsers to include, defaults to None
        :type parent_parsers: ty.Sequence[argparse.ArgumentParser], optional
        :param description: Description of the program, the docstring of the class is used as a default
        :type description: str, optional
        :param intro: Welcome message to print after entering interactive mode, defaults to None
        :type intro: str, optional
        :param stdin: TextIOWrapper to use as the stdin for the interactive shell, defaults to None
        :type stdin: ty.Optional[io.TextIOWrapper], optional
        :param stdout: TextIOWrapper to use as the stdout for the interactive shell, defaults to None
        :type stdout: ty.Optional[io.TextIOWrapper], optional
        :return: Instance of the ArgparseShell
        :rtype: ArgparseShell_T

        """
        namespace = Namespace.from_object(obj, nested_namespaces=nested_namespaces)
        parser = builder.build_arg_parser_from_namespace(
            namespace, program_name=program_name, description=description or inspect.getdoc(obj)
        )
        interactive = builder.build_interactive_shell_from_namespace(
            namespace, prompt=f"{program_name}> ", intro=intro, stdin=stdin, stdout=stdout
        )
        return cls(parser, interactive)

    def main(self, argv: ty.Sequence[str] | None = None) -> None:
        """Run the arg shell. The shell first tries to parse"""
        namespace, _ = self.parser.parse_known_args(argv)

        if constants.ARGPARSE_CALLBACK_FUNCTION_NAME in namespace:
            func = getattr(namespace, constants.ARGPARSE_CALLBACK_FUNCTION_NAME)
            delattr(namespace, constants.ARGPARSE_CALLBACK_FUNCTION_NAME)
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
        namespace_dict = vars(namespace)
        try:
            inspect.signature(func).bind(**namespace_dict)
        except TypeError as exc:
            self.parser.error(str(exc))
        else:
            func(**namespace_dict)

    def _error(self, msg: str):  # pylint: disable=no-self-use
        """Print the error message and exit with an error code

        :param msg: Exit message to print
        :type msg: str
        """
        print(msg, file=sys.stderr)
        sys.exit(1)
