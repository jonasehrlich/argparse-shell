from __future__ import annotations

import types
import typing as ty

import pytest

from argparse_shell import ArgparseShell
from argparse_shell.testing import ArgparseShellRunner

T = ty.TypeVar("T", int, float, str, bytes)


class Calculator:
    """Super calculator"""

    def add(self, a: T, b: T) -> T:
        """Add two numbers

        :param a: First number
        :param b: Second number
        :return: Sum of two numbers
        """
        return a + b

    def div(self, a: float, b: float) -> float:
        """
        Divide numbers

        :param a: First number
        :param b: Second number
        :return: Division of two numbers"""
        return a / b

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers

        :param a: First number
        :param b: Second number
        :return: Product of two numbers
        """
        return a * b


calculator_module = types.ModuleType("calculator")


def add(a, b):
    return a + b


def div(a, b):
    return a / b


setattr(calculator_module, "add", add)
setattr(calculator_module, "div", div)


def test_cli_instance(capsys: pytest.CaptureFixture, subtests):
    """Test that we can run methods through a CLI created with an instance and that the output is printed"""

    drv = Calculator()
    shell = ArgparseShell.from_object(drv, "calc")
    a = 1
    b = 5
    with subtests.test("add"):
        shell.main(["add", str(a), str(b)])
        captured = capsys.readouterr()
        assert captured.out.strip() == str(a + b)

    with subtests.test("div"):
        shell.main(["div", str(a), str(b)])
        captured = capsys.readouterr()
        assert captured.out.strip() == str(a / b)

    with subtests.test("div0"):
        with pytest.raises(ZeroDivisionError):
            shell.main(["div", str(a), "0"])


def test_cli_module(capsys: pytest.CaptureFixture, subtests):
    """Test that we can run methods through a CLI created with a and that the output is printed"""

    shell = ArgparseShell.from_object(calculator_module, "calc")
    a = 1
    b = 5
    with subtests.test("add"):
        shell.main(["add", str(a), str(b)])
        captured = capsys.readouterr()
        assert captured.out.strip() == str(a + b)

    with subtests.test("div"):
        shell.main(["div", str(a), str(b)])
        captured = capsys.readouterr()
        assert captured.out.strip() == str(a / b)

    with subtests.test("div0"):
        with pytest.raises(ZeroDivisionError):
            shell.main(["div", str(a), "0"])


@pytest.mark.skip
def test_interactive_instance(subtests, capsys: pytest.CaptureFixture):
    """Test startup of the interactive shell with a driver instance"""
    drv = Calculator()
    shell = ArgparseShell.from_object(drv, "calc")
    a = 1
    b = 5
    with subtests.test("add"):

        shell = ArgparseShell.from_object(drv, "calc")
        result = ArgparseShellRunner(shell).invoke_interactive("add", a, b)

        result.check()

    with subtests.test("div"):

        shell = ArgparseShell.from_object(drv, "calc")
        result = ArgparseShellRunner(shell).invoke_interactive("div", a, b)

        result.check()

    with subtests.test("div0"):
        with pytest.raises(ZeroDivisionError):

            shell = ArgparseShell.from_object(drv, "calc")
            shell = ArgparseShell.from_object(calculator_module, "calc")
            result = ArgparseShellRunner(shell).invoke_interactive("div", a, 0)
            result.check()


@pytest.mark.skip
def test_interactive_module(subtests, capsys: pytest.CaptureFixture):
    """Test startup of the interactive shell with a driver module"""
    a = 1
    b = 5
    # TODO: assert for output, how to pass the stdout to the pprint_wrapper
    with subtests.test("add"):

        shell = ArgparseShell.from_object(calculator_module, "calc")
        result = ArgparseShellRunner(shell).invoke_interactive("add", a, b)

        result.check()

    with subtests.test("div"):
        shell = ArgparseShell.from_object(calculator_module, "calc")
        result = ArgparseShellRunner(shell).invoke_interactive("div", a, b)

        result.check()

    with subtests.test("div0"):
        with pytest.raises(ZeroDivisionError):

            shell = ArgparseShell.from_object(calculator_module, "calc")
            result = ArgparseShellRunner(shell).invoke_interactive("div", a, 0)
            result.check()
