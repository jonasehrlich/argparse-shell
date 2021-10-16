from unittest import mock

from argparse_shell import builder, namespace, command


def test_build_interactive_shell_from_namespace():
    """Test creation of the interactive shell object from the namespace"""

    func_name = "foo"
    func_mock = mock.MagicMock()
    func_mock.__name__ = func_name
    my_namespace = namespace.Namespace({func_name: command.Command(func_name, func_mock)})
    interactive_shell = builder.build_interactive_shell_from_namespace(my_namespace)
    interactive_method_name = f"do_{func_name}"
    assert hasattr(interactive_shell, interactive_method_name)
    assert hasattr(interactive_shell, f"help_{func_name}")
    interactive_method = getattr(interactive_shell, interactive_method_name)
    # Interactive methods need to be called with an arg string which is parsed inside them
    interactive_method("")
    func_mock.assert_called_once_with()
