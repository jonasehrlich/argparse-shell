import typing as ty
from . import constants


def no_shell_cmd(func: ty.Any) -> ty.Any:
    """
    Decorator to mark a function, that it is not added as a command to the argument parser or the interactive shell
    """

    setattr(func, constants.ARGPARSE_SHELL_CMD_ATTRIBUTE_NAME, False)
    return func


def command(name: str) -> ty.Any:
    """Decorator to explicitly set a name for a command"""

    def inner(func: ty.Any):
        setattr(func, constants.ARGPARSE_SHELL_CMD_ATTRIBUTE_NAME, name)
        return func

    return inner
