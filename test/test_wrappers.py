from __future__ import annotations

import asyncio
import itertools
import typing as ty
from unittest import mock

import pytest
from argparse_shell import wrappers


def return_10(*args, **kwargs):
    return 10


def return_args_and_kwargs(*args, **kwargs):
    return args, kwargs


class Drv:
    def return_value_method(self, *args, **kwargs):
        return return_args_and_kwargs(*args, **kwargs)

    def return_10_method(self, *args, **kwargs):
        return return_10(*args, **kwargs)


@pytest.fixture(scope="module", params=[True, False])
def mockreturn(request):
    """Return a mock object which returns the arguments"""

    if request.param:
        side_effect = Drv().return_value_method
    else:
        side_effect = return_args_and_kwargs

    return_value_mock = mock.Mock(side_effect=side_effect)
    return return_value_mock


@pytest.fixture(scope="module", params=[True, False])
def mockreturn_10(request):
    """Return a mock object which always returns 10"""

    if request.param:
        side_effect = Drv().return_10_method
    else:
        side_effect = return_10

    return_value_mock = mock.Mock(side_effect=side_effect)
    return return_value_mock


@pytest.fixture
def args_kwargs() -> ty.Iterable[ty.Tuple[ty.Tuple[ty.Any, ...], ty.Dict[ty.Any, ty.Any]]]:
    """Return a selection of args and kwargs"""
    args_options = (tuple(), (1,), ("test",), ([1, 3],), ({"test": 1},))
    kwargs_options = (dict(), dict(a=12))
    return itertools.product(args_options, kwargs_options)


def test_pprint_wrapper(subtests, args_kwargs, mockreturn_10: mock.Mock):  # pylint: disable=redefined-outer-name
    """Test that functions wrapped into the pprint_wrapper call pprint.pprint with the result and return it"""

    wrapped = wrappers.pprint_wrapper(mockreturn_10)
    with mock.patch("pprint.pprint") as pprint_mock:
        for args, kwargs in args_kwargs:
            with subtests.test(args=args, kwargs=kwargs):
                result = wrapped(*args, **kwargs)
                assert result == 10
                mockreturn_10.assert_called_once_with(*args, **kwargs)
                pprint_mock.assert_called_once_with(10)

            pprint_mock.reset_mock()
            mockreturn_10.reset_mock()


def test_wrap_interactive_method(subtests, args_kwargs, mockreturn: mock.Mock):  # pylint: disable=redefined-outer-name
    """Test that the wrapper for interactive methods, the wrapper should parse the argument string and"""
    wrapped = wrappers.wrap_interactive_method(mockreturn)

    for args, kwargs in args_kwargs:
        with subtests.test(args=args, kwargs=kwargs):
            obj = object()
            arg_string = " ".join(str(arg) for arg in args)
            kwarg_string = " ".join(f"{key}={value}" for key, value in kwargs.items())
            result = wrapped(obj, f"{arg_string} {kwarg_string}")

            assert result is None
            mockreturn.assert_called_once_with(*args, **kwargs)

        mockreturn.reset_mock()


def test_wrap_corofunc(subtests, args_kwargs, mockreturn: mock.Mock):  # pylint: disable=redefined-outer-name
    """Test the wrapper for a coroutinefunction"""
    orig_side_effect = mockreturn.side_effect

    async def async_side_effect(*args, **kwargs):
        return orig_side_effect(*args, **kwargs)

    mockreturn.side_effect = async_side_effect
    wrapped = wrappers.wrap_corofunc(mockreturn)

    for args, kwargs in args_kwargs:
        with subtests.test(args=args, kwargs=kwargs):
            result = wrapped(*args, **kwargs)
            assert result == (args, kwargs)
            mockreturn.assert_called_once_with(*args, **kwargs)

        mockreturn.reset_mock()


def test_wrap_genfunc():
    """Test the wrapper for generators"""

    def range2(i):
        for idx in range(i):
            yield idx

    m = mock.Mock(side_effect=range2)
    wrapped = wrappers.wrap_generatorfunc(m)
    arg = 10
    result = wrapped(arg)
    m.assert_called_once_with(arg)
    assert result == list(range(arg))


def test_wrap_asyncgenfunc():
    """Test the wrapper for async generators"""

    async def arange(i):
        for idx in range(i):
            yield idx
            await asyncio.sleep(0)

    m = mock.Mock(side_effect=arange)
    wrapped = wrappers.wrap_asyncgeneratorfunc(m)
    arg = 10
    result = wrapped(arg)
    m.assert_called_once_with(arg)
    assert result == list(range(arg))


def test_wrap_datadescriptor(subtests):
    """Test the wrapper function for data descriptors"""

    class Driver:
        def __init__(self, name: str, port: int):
            self._name = name
            self._port = port

        @property
        def port(self) -> int:
            return self._port

        @port.setter
        def port(self, value: int):
            self._port = value

        @property
        def name(self) -> str:
            return self._name

    driver_name = "mydriver"
    port = 10

    with subtests.test(msg="get set property"):
        drv = Driver(driver_name, port)
        wrapped = wrappers.wrap_datadescriptor(Driver.port)

        assert wrapped(drv) == port
        assert wrapped(drv, 0) is None
        assert wrapped(drv) == 0

    with subtests.test(msg="get property"):
        drv = Driver(driver_name, port)
        wrapped = wrappers.wrap_datadescriptor(Driver.name)

        assert wrapped(drv) == driver_name
        with pytest.raises(AttributeError):
            assert wrapped(drv, "new name")
