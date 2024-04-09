from __future__ import annotations

import argparse
import sys
import typing as ty

import docstring_parser

from . import constants, interactive, utils, wrappers
from .namespace import Namespace


def build_interactive_shell_from_namespace(
    namespace: Namespace,
    prompt: str = "cli>",
    intro: str | None = None,
    *,
    stdin: ty.Optional[ty.TextIO] = None,
    stdout: ty.Optional[ty.TextIO] = None,
) -> interactive.InteractiveCmd:
    """Build a interactive shell from a namespace definition

    :param namespace: Namespace to use as a base
    :type namespace: Namespace
    :param prompt: Prompt prefix to use in the interactive shell, defaults to "cli>"
    :type prompt: str, optional
    :param intro: Intro, or welcome message to print after interactive shell start, defaults to None
    :type intro: str, optional
    :param stdin: TextIOWrapper to use as the stdin for the interactive shell, defaults to None
    :type stdin: ty.Optional[ty.TextIO], optional
    :param stdout: TextIOWrapper to use as the stdout for the interactive shell, defaults to None
    :type stdout: ty.Optional[ty.TextIO], optional
    :return: InteractiveCmd
    :rtype: interactive.InteractiveCmd
    """
    shell = interactive.InteractiveCmd(namespace, stdin=stdin, stdout=stdout)
    shell.intro = intro
    shell.prompt = prompt
    return shell


def build_arg_parser_from_namespace(
    namespace: Namespace, program_name: str, description: str | None = None
) -> argparse.ArgumentParser:
    """Build an :py:class:`argparse.ArgumentParser` from a namespace definition. The argument parser will contain
    each function in the namespace as a subcommand with all the arguments as positional arguments.

    :param namespace: Namespace to use as base
    :type namespace: Namespace
    :param program_name: Name of the program
    :type program_name: str
    :param description: Description of the program
    :type description: str, optional
    :return: Created argument parser
    :rtype: argparse.ArgumentParser
    """

    parser = argparse.ArgumentParser(prog=program_name, description=description)
    subparsers = parser.add_subparsers(title="sub commands", help="")
    for name, cmd in namespace.items():

        parse_result = docstring_parser.parse(cmd.docstring())

        sub_cmd_parser = subparsers.add_parser(
            name, help=parse_result.short_description or "", description=cmd.description()
        )

        docstring_params_map = {param.arg_name: param for param in parse_result.params}
        # Add each argument of the callable as a positional argument
        sig = cmd.signature()
        for parameter_name, parameter in sig.parameters.items():
            parameter_kwargs = dict()

            docstring_param = docstring_params_map.get(parameter_name)

            if parameter.default != parameter.empty:
                parameter_kwargs["default"] = parameter.default

            if docstring_param and docstring_param.description:
                parameter_help = docstring_param.description
            else:
                # Fallback to a default help for a parameter
                parameter_help = utils.get_argument_help_string(parameter)

            sub_cmd_parser.add_argument(
                parameter_name, type=utils.eval_literal_value, help=parameter_help, **parameter_kwargs
            )
        sub_cmd_parser.set_defaults(
            **{constants.ARGPARSE_CALLBACK_FUNCTION_NAME: wrappers.pprint_wrapper(cmd.func, sys.stdout)}
        )
    return parser
