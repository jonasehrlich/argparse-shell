from unittest import mock

from argparse_shell import builder


def test_build_namespace_from_object_getter_property():
    """Test namespace building for objects with a getter property"""

    class Driver:
        @property
        def name(self) -> str:
            return "test"

    namespace = builder.build_namespace_from_object(Driver())
    assert list(namespace.keys()) == ["name"]


def test_build_namespace_from_object_getter_setter_property():
    """Test namespace building for objects with a getter / setter property"""

    class Driver:
        @property
        def name(self) -> str:
            return "test"

        @name.setter
        def name(self, value: str):
            ...

    namespace = builder.build_namespace_from_object(Driver())
    assert list(namespace.keys()) == ["name"]


def test_build_namespace_from_object_coroutine():
    """Test namespace building for objects with a getter / setter property"""

    class Driver:
        async def my_coro(self):
            ...

    namespace = builder.build_namespace_from_object(Driver())
    assert list(namespace.keys()) == ["my-coro"]


def test_build_namespace_from_object_method():
    """Test namespace building for objects with methods"""

    class Driver:
        def my_method(self):
            ...

    namespace = builder.build_namespace_from_object(Driver())
    assert list(namespace.keys()) == ["my-method"]


def test_build_namespace_from_object_private_method():
    """Test namespace building for objects with methods"""

    class Driver:
        def _my_method(self):
            ...

    namespace = builder.build_namespace_from_object(Driver())
    assert not namespace


def test_build_namespace_from_object_other_attribute():
    """Test normal attributes are not included in the namespace"""

    class Driver:
        def __init__(self) -> None:
            self.name = 10

    namespace = builder.build_namespace_from_object(Driver())
    assert not namespace


def test_build_interactive_shell_from_namespace():
    """Test creation of the interactive shell object from the namespace"""

    func_name = "foo"
    func_mock = mock.MagicMock()
    func_mock.__name__ = func_name
    namespace = {func_name: func_mock}
    interactive_shell = builder.build_interactive_shell_from_namespace(namespace)
    interactive_method_name = f"do_{func_name}"
    assert hasattr(interactive_shell, interactive_method_name)
    assert hasattr(interactive_shell, f"help_{func_name}")
    interactive_method = getattr(interactive_shell, interactive_method_name)
    # Interactive methods need to be called with an arg string which is parsed inside them
    interactive_method("")
    func_mock.assert_called_once_with()
