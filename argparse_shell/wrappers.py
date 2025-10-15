import asyncio
import functools
import pprint
import sys
import typing as ty

from . import utils

P = ty.ParamSpec("P")
T = ty.TypeVar("T")


def pprint_wrapper(func: ty.Callable[P, T], stream: ty.IO[str]) -> ty.Callable[P, T]:
    """Get a wrapper around a function that pretty-prints the output before returning

    :param func: Callable to wrap
    :type func: ty.Callable
    :param stream: Stream to write the return value of the callable to
    :type stream: ty.IO[str]
    :return: Wrapped function
    :rtype: ty.Callable
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        result = func(*args, **kwargs)
        if result is not None:
            output = pprint.pformat(result)
            stream.write(output)
        return result

    return wrapper


def wrap_interactive_method(func: ty.Callable[..., T]) -> ty.Callable[[str], None]:
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
    def wrapper(arg_string: str) -> None:
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


def wrap_corofunc(corofunc: ty.Callable[P, ty.Coroutine[None, None, T]]) -> ty.Callable[P, T]:
    """Get a wrapper for a coroutine function that executes the coroutine on the event loop"""

    @functools.wraps(corofunc)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return _run_on_loop(corofunc(*args, **kwargs))

    return wrapper


def wrap_datadescriptor(descriptor: ty.Any) -> ty.Callable[[ty.Any], ty.Any] | ty.Callable[[ty.Any, str], None]:
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

    def wrapper(obj: ty.Any, *args: ty.Any) -> ty.Any | None:  # pylint: disable=inconsistent-return-statements
        if not args:
            # No args, so the getter needs to be called
            return descriptor.fget(obj)
        if len(args) == 1:
            # One argument so call the setter
            if descriptor.fset is None:
                raise AttributeError(f"Can't set attribute '{name}'")
            descriptor.fset(obj, *args)
            return None

        # Descriptors only support one or no argument, so raise if
        raise TypeError(f"Invalid number of arguments for descriptor {obj.__class__.__name__}.{name}")

    wrapper.__name__ = name
    wrapper.__doc__ = descriptor.fget.__doc__

    return wrapper


def wrap_generatorfunc(genfunc: ty.Callable[P, ty.Generator[T, None, None]]) -> ty.Callable[P, list[T]]:
    """Get a function wrapper for a generatorfunction"""

    @functools.wraps(genfunc)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[T]:
        gen = genfunc(*args, **kwargs)
        return list(gen)

    return wrapper


def wrap_asyncgeneratorfunc(asyncgenfunc: ty.Callable[P, ty.AsyncGenerator[T, None]]) -> ty.Callable[P, list[T]]:
    """Get a function wrapper for a generatorfunction"""

    @functools.wraps(asyncgenfunc)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[T]:
        async def consume_asyncgen() -> list[T]:
            gen = asyncgenfunc(*args, **kwargs)
            return [item async for item in gen]

        return _run_on_loop(consume_asyncgen())

    return wrapper


def _run_on_loop(coro: ty.Coroutine[None, None, T]) -> T:
    """Run a coroutine on the event loop. In future releases of Python, :py:func:`asyncio.get_event_loop`
    will be an alias of :py:func:`asyncio.get_running_loop`. This method either re-uses a running loop, or uses the
    :py:func:`asyncio.run` function."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        return loop.run_until_complete(coro)
