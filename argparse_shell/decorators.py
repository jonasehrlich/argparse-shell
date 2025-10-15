import collections.abc
import typing as ty

from . import constants

T = ty.TypeVar("T", bound=collections.abc.Callable[..., ty.Any])


def no_shell_cmd(func: T) -> T:
    """
    Decorator to mark a function, that it is not added as a command to the argument parser or the interactive shell
    """

    setattr(func, constants.ARGPARSE_SHELL_CMD_ATTRIBUTE_NAME, False)
    return func


def command_name(name: str) -> collections.abc.Callable[[T], T]:
    """Decorator to explicitly set a name for a command"""

    def inner(func: T) -> T:
        setattr(func, constants.ARGPARSE_SHELL_CMD_ATTRIBUTE_NAME, name)
        return func

    return inner
