from __future__ import annotations

import argparse
import cmd
import inspect
import sys
import textwrap
import typing as ty

from . import constants, utils, wrappers
from .interactive import InteractiveCmd

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
        parent_parsers: ty.Sequence[argparse.ArgumentParser] = None,
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
        namespace = _build_namespace_from_object(obj)
        parser = _build_arg_parser_from_namespace(namespace, program_name=program_name, parent_parsers=parent_parsers)
        interactive = _build_interactive_shell_from_namespace(namespace, prompt=f"{program_name}> ", intro=intro)
        return cls(parser, interactive)

    def main(self):
        """Run the arg shell. The shell first tries to parse"""
        namespace, _ = self.parser.parse_known_args()

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


def _build_interactive_shell_from_namespace(
    namespace: Namespace, prompt: str = "cli>", intro: str = None
) -> InteractiveCmd:
    """Build a interactive shell from a namespace definition

    :param namespace: Namespace to use as a base
    :type namespace: Namespace
    :param prompt: Prompt prefix to use in the interactive shell, defaults to "cli>"
    :type prompt: str, optional
    :param intro: Intro, or welcome message to print after interactive shell start, defaults to None
    :type intro: str, optional
    :return: Subclass of InteractiveCmd
    :rtype: cmd.Cmd
    """
    class_namespace = dict()
    for command, func in namespace.items():

        cmd_func_name = f"do_{func.__name__}"
        help_func_name = f"help_{func.__name__}"
        class_namespace[cmd_func_name] = wrappers.interactive_method_wrapper(wrappers.pprint_wrapper(func))
        class_namespace[help_func_name] = get_interactive_help_function(command, func)
    class_namespace["prompt"] = prompt
    class_namespace["intro"] = intro

    interactive_class = type("InteractiveCmdShell", (InteractiveCmd,), class_namespace)
    return interactive_class()


def _build_arg_parser_from_namespace(
    namespace: Namespace, program_name: str, parent_parsers: ty.Sequence[argparse.ArgumentParser] = None
) -> argparse.ArgumentParser:
    if parent_parsers is None:
        parent_parsers = list()

    parser = argparse.ArgumentParser(prog=program_name, parents=parent_parsers)
    subparsers = parser.add_subparsers(help="sub-command help")
    for name, func in namespace.items():
        docstring = utils.get_docstring(func)
        # TODO: specify arguments on the sub parsers
        sub_cmd_parser = subparsers.add_parser(name, help=docstring)
        sub_cmd_parser.add_argument("args", nargs="*", help=get_argument_help_string(func))
        sub_cmd_parser.set_defaults(**{constants.ARGPARSE_CALLBACK_FUNCTION_NAME: wrappers.pprint_wrapper(func)})
    return parser


def _build_namespace_from_object(obj: ty.Any) -> ty.Dict[str, ty.Callable]:
    """Build a namespace from an object. The namespace is a mapping of command names to callback functions.
    This layer wraps coroutine functions and descriptors in functions, to allow them being called directly.

    :param obj: Object to build the namespace from
    :type obj: ty.Any
    :return: Mapping of command names defined in an object
    :rtype: ty.Dict[str, ty.Callable]
    """
    namespace = dict()
    for name, value in inspect.getmembers(obj.__class__, utils.is_supported_command_type):
        if not utils.is_shell_cmd(value):
            continue
        # TODO: add support for descriptors
        # if inspect.isgetsetdescriptor(value):
        #    cmd_name = utils.python_name_to_dashed(name)
        #    namespace[cmd_name] = wrappers.getsetdescriptor_wrapper(value)
        if inspect.iscoroutinefunction(value):
            cmd_name = utils.get_command_name(value)
            namespace[cmd_name] = wrappers.corofunc_wrapper(getattr(obj, name))
        elif inspect.ismethod(value) or inspect.isfunction(value):
            cmd_name = utils.get_command_name(value)
            namespace[cmd_name] = getattr(obj, name)

    return namespace


def get_argument_help_string(func: ty.Callable) -> str:
    """Get the help string for a command line argument"""
    sig = inspect.signature(func)
    return f"{func.__name__}{sig}"


def get_interactive_help_function(command: str, func: ty.Callable):
    """Creates a help function to use in the interactive mode

    :param func: Function to create the help function for
    :type func: ty.Callable
    """
    help_text = textwrap.dedent(
        f"""
    {command}
    {'-'*len(command)}

    {inspect.signature(func)}

    {utils.get_docstring(func)}
    """
    )

    def do_help(self):  # pylint: disable=unused-argument
        print(help_text)

    do_help.__name__ = f"help_{func.__name__}"
    return do_help
