import typing as ty
from unittest import mock

import pytest
from argparse_shell.interactive import InteractiveCmd
from argparse_shell.namespace import Namespace, Command
import functools

cmd_name = "some-action"

help_mock = functools.partial(print, "help", cmd_name)


def return_all(*args):
    return args


@pytest.fixture()
def namespace():
    cmd = Command(cmd_name, mock.Mock(side_effect=return_all))
    cmd._interactive_help_method = mock.Mock(side_effect=help_mock)
    namespace_ = Namespace(**{cmd_name: cmd})
    return namespace_


def get_argstr(*args: ty.Any):
    return " ".join(str(arg) for arg in args)


def test_command(namespace, subtests, capsys):
    with subtests.test("no args"):
        shell = InteractiveCmd(namespace)
        shell.onecmd(cmd_name)
        namespace[cmd_name].func.assert_called_once()
    namespace[cmd_name].func.reset_mock()

    with subtests.test("positional args"):
        shell = InteractiveCmd(namespace)
        args = ("test", 1, dict(test=15))
        shell.onecmd(f"{cmd_name} " + get_argstr(*args))
        namespace[cmd_name].func.assert_called_once_with(*args)
    namespace[cmd_name].func.reset_mock()


def test_interactive_command_not_found(namespace, subtests, capsys: pytest.CaptureFixture):
    """Test behavior for unknown commands, this includes commands with underscores"""
    for wrong_command in (cmd_name.replace("-", "_"), "asdf"):
        with subtests.test(f"wrong command: {wrong_command}"):
            shell = InteractiveCmd(namespace)
            shell.onecmd(wrong_command)
            captured = capsys.readouterr()
            assert captured.out == f"*** Unknown syntax: {wrong_command}\n"


def test_dashed_command_help(namespace, capsys: pytest.CaptureFixture):
    """Test that the interactive help is printed correctly for dashed commands"""
    shell = InteractiveCmd(namespace)
    shell.onecmd("help " + cmd_name)
    captured = capsys.readouterr()
    assert captured.out == f"help {cmd_name}\n"


def test_command_complete(namespace, capsys: pytest.CaptureFixture):
    """Test completion behavior for commands"""
    shell = InteractiveCmd(namespace)
    assert shell.completenames(cmd_name[:3]) == [cmd_name]
