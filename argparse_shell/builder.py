from __future__ import annotations

import argparse
import inspect
import textwrap
import typing as ty

from . import constants, utils, wrappers, interactive

if ty.TYPE_CHECKING:
    from .argparse_shell import Namespace


def build_interactive_shell_from_namespace(
    namespace: Namespace, prompt: str = "cli>", intro: str = None
) -> interactive.InteractiveCmd:
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
        class_namespace[cmd_func_name] = wrappers.wrap_interactive_method(wrappers.pprint_wrapper(func))
        class_namespace[help_func_name] = get_interactive_help_function(command, func)
    class_namespace["prompt"] = prompt
    class_namespace["intro"] = intro

    interactive_class = type("InteractiveCmdShell", (interactive.InteractiveCmd,), class_namespace)
    return interactive_class()


def build_arg_parser_from_namespace(namespace: Namespace, program_name: str) -> argparse.ArgumentParser:
    """Build an :py:class:`argparse.ArgumentParser` from a namespace definition. The argument parser will contain
    each function in the namespace as a subcommand with all the arguments as positional arguments.

    :param namespace: Namespace to use as base
    :type namespace: Namespace
    :param program_name: Name of the program
    :type program_name: str
    :return: Created argument parser
    :rtype: argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser(prog=program_name)
    subparsers = parser.add_subparsers(title="sub commands", description="valid subcommands", help="")
    for name, func in namespace.items():
        docstring = utils.get_docstring(func)
        # TODO: specify arguments on the sub parsers
        sub_cmd_parser = subparsers.add_parser(name, help=docstring)
        sub_cmd_parser.add_argument("args", nargs="*", help=get_argument_help_string(func))
        sub_cmd_parser.set_defaults(**{constants.ARGPARSE_CALLBACK_FUNCTION_NAME: wrappers.pprint_wrapper(func)})
    return parser


def build_namespace_from_object(obj: ty.Any) -> ty.Dict[str, ty.Callable]:
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
        if inspect.isdatadescriptor(value):
            cmd_name = utils.python_name_to_dashed(name)
            namespace[cmd_name] = wrappers.wrap_datadescriptor(obj, name, value)
        elif inspect.iscoroutinefunction(value):
            cmd_name = utils.get_command_name(value)
            namespace[cmd_name] = wrappers.wrap_corofunc(getattr(obj, name))
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
