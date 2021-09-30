import asyncio
import functools
import pprint
import typing as ty

from . import utils


def pprint_wrapper(func: ty.Callable) -> ty.Callable:
    """Get a wrapper around a function that pretty-prints the output before returning"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result is not None:
            pprint.pprint(result)
        return result

    return wrapper


def interactive_method_wrapper(func: ty.Callable) -> ty.Callable:
    """Get a wrapper for a callable, to be used in a :py:class:`cmd.Cmd` interactive shell.
    The wrapper function parses the arguments and calls the wrapped callable and does **not** return
    the return value, as this would lead the interactive loop to stop

    :param func: Callable to be wrapped
    :type func: ty.Callable
    :return: Wrapper around the callable
    :rtype: ty.Callable
    """

    @functools.wraps(func)
    def wrapper(self, arg_string):  # pylint: disable=unused-argument
        args, kwargs = utils.parse_arg_string(arg_string)
        func(*args, **kwargs)
        # Do not return anything from the wrapper, because this will trigger the stop of the command loop

    return wrapper


def corofunc_wrapper(corofunc: ty.Callable):
    """Get a wrapper for a coroutine function that executes the coroutine on the event loop"""

    @functools.wraps(corofunc)
    def wrapper(self, *args, **kwargs):  # pylint: disable=unused-argument
        return asyncio.get_event_loop().run_until_complete(corofunc(*args, **kwargs))

    return wrapper


def getsetdescriptor_wrapper(descriptor):
    """Get a function wrapper for a getsetdescriptor"""

    def wrapper(self, *args):
        if not args:
            return descriptor.fget(self)
        if len(args) == 1:
            descriptor.fset(self, args[0])
        raise ValueError(f"Invalid number of arguments for descriptor {self.__class__.__name__}.{descriptor.__name__}")

    wrapper.__name__ = descriptor.fget.__name__
    wrapper.__doc__ = descriptor.fget.__doc__

    return wrapper
