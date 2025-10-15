import asyncio
import functools
import pprint
import sys
import typing as ty

from . import utils

try:
    import rich.pretty

    __RICH_AVAILABLE__ = True
except ImportError:
    __RICH_AVAILABLE__ = False


def pprint_wrapper(func: ty.Callable, stream: ty.TextIO) -> ty.Callable:
    """Get a wrapper around a function that pretty-prints the output before returning

    :param func: Callable to wrap
    :type func: ty.Callable
    :param stream: Stream to write the return value of the callable to
    :type stream: ty.TextIO
    :return: Wrapped function
    :rtype: ty.Callable
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if result is not None:
            if __RICH_AVAILABLE__:
                output = rich.pretty.pprint(result)
            else:
                output = pprint.pformat(result)
                stream.write(output)
        return result

    return wrapper


def wrap_interactive_method(func: ty.Callable) -> ty.Callable:
    """Get a wrapper for a callable, to be used in a :py:class:`cmd.Cmd` interactive shell.
    The wrapper function expects two arguments, the instance (`self`) and the argument string.
    The argument string is parsed to Python literals which are then passed into the wrapped method.

    Afterwards, the return value of the wrapped function / method is ignored and **not** returned,
    as this would lead the interactive loop to stop. In order to print the return value,
    consider wrapping the callable into a decorator such as :py:func:`pprint_wrapper` before
    passing it into :py:func:`wrap_interactive_method`.

    :param func: Callable to be wrapped
    :type func: ty.Callable
    :return: Wrapper around the callable
    :rtype: ty.Callable
    """

    @functools.wraps(func)
    def wrapper(arg_string: str):
        args, kwargs = utils.parse_arg_string(arg_string)
        try:
            func(*args, **kwargs)
        except Exception as exc:
            # Catch all exceptions raised by interactive methods, because errors should not exit the
            # shell
            exc_type, _, tb = sys.exc_info()
            utils.handle_interactive_error(exc_type, exc, tb)
        # Do not return anything from the wrapper, because this will trigger the stop of the command loop

    return wrapper


def wrap_corofunc(corofunc: ty.Callable):
    """Get a wrapper for a coroutine function that executes the coroutine on the event loop"""

    @functools.wraps(corofunc)
    def wrapper(*args, **kwargs):
        return _run_on_loop(corofunc(*args, **kwargs))

    return wrapper


def wrap_datadescriptor(descriptor: ty.Any) -> ty.Callable:
    """Get a function wrapper for a descriptor on a object.

    The function wrapper will call the getter if no argument is passed into the wrapper,
    if one argument is passed in, the setter is called. For all other numbers of arguments,
    a :py:class:`TypeError` is raised.

    :param descriptor: Descriptor object
    :type descriptor:
    :param name: Name of the attribute the descriptor handles
    :type name: str
    :return: Function wrapping the descriptor
    :rtype: ty.Callable
    """

    func = descriptor.fget or descriptor.fset
    name = func.__name__

    def wrapper(obj: ty.Any, *args):  # pylint: disable=inconsistent-return-statements
        if not args:
            # No args, so the getter needs to be called
            return descriptor.fget(obj)
        if len(args) == 1:
            # One argument so call the setter
            if descriptor.fset is None:
                raise AttributeError(f"Can't set attribute '{name}'")
            descriptor.fset(obj, *args)
            return

        # Descriptors only support one or no argument, so raise if
        raise TypeError(f"Invalid number of arguments for descriptor {obj.__class__.__name__}.{name}")

    wrapper.__name__ = name
    wrapper.__doc__ = descriptor.fget.__doc__

    return wrapper


def wrap_generatorfunc(genfunc: ty.Callable):
    """Get a function wrapper for a generatorfunction"""

    @functools.wraps(genfunc)
    def wrapper(*args, **kwargs):
        gen = genfunc(*args, **kwargs)
        return list(gen)

    return wrapper


def wrap_asyncgeneratorfunc(asyncgenfunc: ty.Callable):
    """Get a function wrapper for a generatorfunction"""

    @functools.wraps(asyncgenfunc)
    def wrapper(*args, **kwargs):
        async def consume_asyncgen():
            gen: ty.AsyncGenerator = asyncgenfunc(*args, **kwargs)
            return [item async for item in gen]

        return _run_on_loop(consume_asyncgen())

    return wrapper


def _run_on_loop(coro: ty.Coroutine):
    """Run a coroutine on the event loop. In future releases of Python, :py:func:`asyncio.get_event_loop_loop`
    will be an alias of :py:func:`asyncio.get_running_loop`. This method either re-uses a running loop, or uses the
    :py:func:`asyncio.run` function."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        runner = asyncio.run
    else:
        runner = loop.run_until_complete
    return runner(coro)
