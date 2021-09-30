import ast
import inspect
import re
import textwrap
import typing as ty

from . import constants


def parse_arg_string(arg_string: str) -> ty.Tuple[ty.Tuple[ty.Any, ...], ty.Dict[str, ty.Any]]:
    """Parse a string of arguments to positional and keyword arguments.
    This currently supports only parsing of literal values.

    >>> arg_string = "1 2 name=myvalue
    >>> parse_arg_string(arg_string)
    ((1, 2), {"name": "myvalue"})

    :param arg_string: Argument string separated by spaces
    :type arg_string: str
    :raises ValueError: Raised if the value cannot be parsed
    :return: 2-tuple of a tuple of positional arguments and a dict of keyword arguments
    :rtype: ty.Tuple[ty.Tuple[ty.Any, ...], ty.Dict[str, ty.Any]]
    """
    args = list()
    kwargs = dict()
    for item in arg_string.split():
        split_result = item.split("=", 1)
        if len(split_result) == 1:
            args.append(_eval_literal_value(split_result[0]))
        elif len(split_result) == 2:
            kwargs[split_result[0]] = _eval_literal_value(split_result[1])
        else:
            raise ValueError(f"Cannot parse argument string item: '{item}'")
    return tuple(args), kwargs


def _eval_literal_value(value: str) -> ty.Any:
    """Evaluate a string to a literal value

    :param value: Value to evaluate
    :type value: str
    :return: Literal value the string is evaluated to
    :rtype: ty.Any
    """
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError) as exc:
        try:
            return ast.literal_eval(f"'{value}'")
        except (SyntaxError, ValueError):
            raise exc  # pylint: disable=raise-missing-from


def is_shell_cmd(func: ty.Callable) -> bool:
    """Return whether a callable should be added as a shell command.
    This function returns `False` if:
    * The name of the callable starts with an underscore
    * The attribute `__argparse_shell_cmd__` is set to `False`. This can be done using the `@no_shell_cmd` decorator

    :param func: Callable to check
    :type func: ty.Callable
    :return: Whether a callable should be added as a shell command
    :rtype: bool
    """
    if func.__name__.startswith("_"):
        return False
    return getattr(func, constants.ARGPARSE_SHELL_CMD_ATTRIBUTE_NAME, True)


def python_name_to_dashed(name: str) -> str:
    """Make a dashed string from a valid Python name

    :param name: Python name
    :type name: str
    :return: Dashed string
    :rtype: str
    """
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", name)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1-\2", name)
    name.replace("_", "-")
    return name.lower()


def get_command_name(func: ty.Callable) -> str:
    """Get the command name for a callable. The command name can be defined using the
    :py:func:`~argparse_shell.decorators.command decorator`.

    :param func: Callable to get the command name for
    :type func: ty.Callable
    :return: Command name for the callable
    :rtype: str
    """
    fixed_name = getattr(func, constants.ARGPARSE_SHELL_CMD_ATTRIBUTE_NAME, False)
    if fixed_name and isinstance(fixed_name, str):
        return fixed_name
    return python_name_to_dashed(func.__name__)


def get_docstring(func: ty.Any) -> str:
    """Return a valid docstring for any object"""

    return textwrap.dedent((inspect.getdoc(func) or f"{func.__name__} {func.__class__.__name__}").strip())


def is_supported_command_type(value: ty.Any) -> bool:
    """Return whether an attribute is supported as a command implementation

    :param value: Attribute value
    :type value: ty.Any
    :return: Whether the attribute can be used as a command
    :rtype: bool
    """
    for predicate in (inspect.iscoroutinefunction, inspect.ismethod, inspect.isfunction):
        if predicate(value):
            return True
    return False
