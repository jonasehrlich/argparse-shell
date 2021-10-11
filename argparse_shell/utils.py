import ast
import inspect
import re
import textwrap
import typing as ty

from . import constants


def split_to_literals(
    value: str,
    sep: str = " ",
    pairs: ty.Sequence[ty.Tuple[str, str]] = (("(", ")"), ("[", "]"), ("{", "}")),
    quotes: ty.Sequence[str] = "\"'",
) -> str:
    """
    Split a string of Python literals into multiple literals.

    The string is split by `sep` but parts inside pairs or quotes are considered unbreakable.
    Use :py:func:`itertools.islice` to slice the splits.

    This implementation is based on
    https://www.daniweb.com/programming/software-development/code/426990/split-string-except-inside-brackets-or-quotes

    :param value: String to separate
    :type value: str
    :param sep: Seperator to split the string by, defaults to " "
    :type sep: str, optional
    :param pairs: Iterable of 2-tuples containing the ("start", "stop") pairs between which no splits can happen,
                  defaults to ``(("(", ")"), ("[", "]"), ("{", "}"))``
    :param quotes: Sequence of characters to consider as quotes
    :raises IndexError: Raised if no matching quotes or brackets can be found
    :yield:
    :rtype: str
    """
    value = value.strip()
    if not value:
        # No value, raise the StopIteration on the first call of the generator
        return

    # Create a map of left pair characters to right pair characters
    pair_map = dict(pairs)

    value_length = len(value)
    item_start_idx = 0  # Start index of the current item
    idx = 0  # Global iteration index

    # Use an index-based while loop to do quick jumps on the index
    while idx < value_length:
        character = value[idx]
        if value[idx:].startswith(sep):
            # A separator was reached, yield the start of the current item to the current index
            yield value[item_start_idx:idx]

            # Move idx to the next character that is not a separator
            if len(sep) == 1:
                # The separator is a single character, use the builtin lstrip method
                idx = value_length - len(value[idx:].lstrip(sep))
            else:
                # The separator is a sequence of characters, iteratively iterate until
                # we don't find a separator anymore
                while value[idx:].startswith(sep):
                    idx = idx + len(sep)
            item_start_idx = idx

        elif character in quotes:
            # We are in a quoted section, jump to the close of the quote
            quote_start_idx = idx

            exc = IndexError(f"Unmatched quote at index {quote_start_idx}: {value}")
            idx = find_nth_with_raise(value, character, idx + 1, exc=exc)
            # Index is at the closing quote, increment to next character
            idx += 1
        elif character in pair_map:
            # We are in a secton that starts with a start element defined in the pairs,
            # so we need to find the end index of this pair

            # Get the close character to search for
            close_character = pair_map[character]

            # Get the possible first end of the pair
            exc = IndexError(
                f"Unmatched closing character '{close_character}' for '{character}' at index {idx}: {value}"
            )
            # Move index to after the open
            idx += 1
            inner_end_idx = find_nth_with_raise(value, close_character, idx, exc=exc)

            # Find the number of nested pair starts in the inner string
            num_nested = value[idx:inner_end_idx].count(character)
            if num_nested:
                inner_end_idx = find_nth_with_raise(value, close_character, idx, occurrence=num_nested, exc=exc)

            # No further starting brackets were found until the first closing bracket, so further nesting is
            # discovered
            idx = inner_end_idx
        else:
            idx += 1

    if value[item_start_idx:]:
        yield value[item_start_idx:]


def find_nth_with_raise(
    haystack: str, needle: str, start: int = 0, end: int = None, occurrence: int = 0, exc: Exception = None
) -> int:
    """
    Find the nth occurrence of a substring in a string and raise a specific exception if it is not found

    :param haystack: String to find the item in
    :type haystack: str
    :param needle: Substring to find
    :type needle: str
    :param occurrence: Occurrence to find in the string
    :type occurrence: int
    :param start: Index to start, defaults to 0
    :type start: int, optional
    :param exc: Exception to raise in the error case, defaults to None, which will result in an `IndexError`
    :type exc: Exception, optional
    :return: Index of the n-th occurrence of the substring
    """
    idx = find_nth(haystack, needle, start, end, occurrence)
    if idx < 0:
        occurrence_str = f"{occurrence}. occurrence of " if occurrence else ""
        exc = exc or IndexError(f"Did not find {occurrence_str}'{needle}' in '{haystack[start:]}'")
        raise exc
    return idx


def find_nth(haystack: str, needle: str, start: int = 0, end: int = None, occurrence: int = 0) -> int:
    """Find the nth occurrence of a substring in a string

    :param haystack: String to find the item in
    :type haystack: str
    :param needle: Substring to find
    :type needle: str
    :param start: Index to start, defaults to 0
    :type start: int, optional
    :param end: Index to end the search, defaults to None
    :type end: int, optional
    :param occurrence: Occurrence to find in the string, defaults to 0
    :type occurrence: int, optional
    :return: Index of the n-th occurrence of the substring, returns -1 if not found
    :rtype: int
    """
    end = end if end is not None else len(haystack)
    if not occurrence:
        # If we need to find the first occurrence fall back to the builtin find method
        return haystack.find(needle, start, end)

    haystack = haystack[start:end]
    parts = haystack.split(needle, occurrence + 1)
    if len(parts) <= occurrence + 1:
        return -1
    return (start + len(haystack)) - len(parts[-1]) - len(needle)


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
    for item in split_to_literals(arg_string):
        split_result = item.split("=", 1)
        if len(split_result) == 1:
            args.append(eval_literal_value(split_result[0]))
        elif len(split_result) == 2:
            kwargs[split_result[0]] = eval_literal_value(split_result[1])
        else:
            raise ValueError(f"Cannot parse argument string item: '{item}'")
    return tuple(args), kwargs


def eval_literal_value(value: str) -> ty.Any:
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
    return name.replace("_", "-").lower()


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
