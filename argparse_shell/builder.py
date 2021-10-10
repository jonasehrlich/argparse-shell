from __future__ import annotations

import argparse
import inspect
import typing as ty

from . import constants, interactive, wrappers
from .namespace import Namespace


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
    for _, cmd in namespace.items():

        class_namespace[cmd.interactive_method_name] = cmd.interactive_method()
        class_namespace[cmd.interactive_help_method_name] = cmd.interactive_help_method()
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
    for name, cmd in namespace.items():
        docstring = cmd.docstring()
        # TODO: specify arguments on the sub parsers
        sub_cmd_parser = subparsers.add_parser(name, help=docstring)

        # Add each argument of the callable as a positional argument
        sig = cmd.signature()
        for parameter_name, parameter in sig.parameters.items():
            parameter_kwargs = dict()
            if parameter.default != parameter.empty:
                parameter_kwargs["default"] = parameter.default
            sub_cmd_parser.add_argument(parameter_name, help=str(parameter), **parameter_kwargs)
        sub_cmd_parser.set_defaults(**{constants.ARGPARSE_CALLBACK_FUNCTION_NAME: wrappers.pprint_wrapper(cmd.func)})
    return parser



def get_argument_help_string(func: ty.Callable) -> str:
    """Get the help string for a command line argument"""
    sig = inspect.signature(func)
    return f"{func.__name__}{sig}"
