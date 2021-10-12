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
    def wrapper(_, arg_string: str):
        args, kwargs = utils.parse_arg_string(arg_string)
        func(*args, **kwargs)
        # Do not return anything from the wrapper, because this will trigger the stop of the command loop

    return wrapper


def wrap_corofunc(corofunc: ty.Callable):
    """Get a wrapper for a coroutine function that executes the coroutine on the event loop"""

    @functools.wraps(corofunc)
    def wrapper(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(corofunc(*args, **kwargs))

    return wrapper


def wrap_datadescriptor(obj: ty.Any, name: str, descriptor: ty.Any):
    """Get a function wrapper for a descriptor on a object.

    The function wrapper will call the getter if no argument is passed into the wrapper,
    if one argument is passed in, the setter is called. For all other numbers of arguments,
    a :py:class:`TypeError` is raised.

    :param obj: Instance of the class the descriptor lives on
    :type obj: ty.Any
    :param name: Name of the attribute the descriptor handles
    :type name: str
    :param descriptor: Descriptor object
    :type descriptor:
    """

    def wrapper(*args):  # pylint: disable=inconsistent-return-statements
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

        return asyncio.get_event_loop().run_until_complete(consume_asyncgen())

    return wrapper
