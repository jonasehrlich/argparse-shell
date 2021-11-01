import types
from unittest import mock

from argparse_shell.command import UnboundCommand, WrappedCommandType


def test_command_get_docstring():
    """Test creation of docstrings from existing methods"""

    def no_docstring():
        ...

    assert UnboundCommand("test", no_docstring, WrappedCommandType.FUNCTION).docstring() == "no_docstring function"

    expected_docstring = "Hello this is a docstring\nwhich should get dedented"

    def with_docstring():
        """Hello this is a docstring
        which should get dedented"""

    assert UnboundCommand("Test", with_docstring, WrappedCommandType.FUNCTION).docstring() == expected_docstring

    def with_docstring2():
        """
        Hello this is a docstring
        which should get dedented
        """

    assert UnboundCommand("Test", with_docstring2, WrappedCommandType.FUNCTION).docstring() == expected_docstring


def test_unbound_command_bind(subtests):
    """Test binding of unbound commands"""
    with subtests.test("function"):

        def foo():
            ...

        unbound_cmd = UnboundCommand.from_callable("foo", foo)
        cmd = unbound_cmd.bind(None)
        assert unbound_cmd.func is foo
        assert cmd.func is foo

    with subtests.test("module"):

        def module_foo():
            ...

        mod = types.ModuleType("my_module")
        mod.module_foo = module_foo

        unbound_cmd = UnboundCommand.from_callable("foo", mod.module_foo)
        cmd = unbound_cmd.bind(mod)
        assert unbound_cmd.func is mod.module_foo
        assert cmd.func is mod.module_foo

    with subtests.test("class classmethod"):

        class DriverClassmethod:
            @classmethod
            def foo(cls):
                ...

        drv = DriverClassmethod()
        unbound_cmd = UnboundCommand.from_callable("foo", drv.__class__.foo)
        cmd = unbound_cmd.bind(drv)

        assert unbound_cmd.func == drv.foo
        assert cmd.func == drv.foo
        assert cmd.func == DriverClassmethod.foo

    with subtests.test("class staticmethod"):

        class DriverStaticmethod:
            @staticmethod
            def foo():
                ...

        drv = DriverStaticmethod()
        unbound_cmd = UnboundCommand.from_callable("foo", drv.__class__.foo)

        cmd = unbound_cmd.bind(drv)
        assert unbound_cmd.func is drv.foo
        assert cmd.func is drv.foo
        assert cmd.func is DriverStaticmethod.foo

    class Driver:
        def foo(self):
            ...

    with subtests.test("class"):
        drv = Driver()
        unbound_cmd = UnboundCommand.from_callable("foo", Driver.foo)

        cmd = unbound_cmd.bind(drv)

        assert unbound_cmd.func == Driver.foo
        assert cmd.func == drv.foo

    with subtests.test("instance"):

        drv = Driver()
        unbound_cmd = UnboundCommand.from_callable("foo", drv.foo)

        cmd = unbound_cmd.bind(drv)

        assert unbound_cmd.func == drv.foo
        assert cmd.func == drv.foo


def test_for_namespace():
    """Test multiple nesting of namespaces concatenates the command name"""

    def foo():
        ...

    namespaces = ("hello", "this", "is", "a", "tree")
    unbound_cmd = UnboundCommand.from_callable("foo", foo)
    for namespace in reversed(namespaces):
        unbound_cmd = unbound_cmd.for_namespace(namespace)
    assert unbound_cmd.name == f"{'-'.join(namespaces)}-foo"
    assert unbound_cmd.parent_namespaces == namespaces


def test_unbound_command_bind_nested_class(subtests):
    """Test binding of unbound commands for nested namespaces in classes"""
    method_mock = mock.Mock()

    class Nested:
        def instancemethod_foo(self, *args, **kwargs):
            method_mock(self, *args, **kwargs)

        @classmethod
        def classmethod_foo(cls, *args, **kwargs):
            method_mock(cls, *args, **kwargs)

        @staticmethod
        def staticmethod_foo(*args, **kwargs):
            method_mock(*args, **kwargs)

    class OuterWithProperty:
        def __init__(self):
            self._nested = Nested()

        @property
        def nested(self):
            return self._nested

    class OuterWithClassAttribute:
        nested = Nested()

    class OuterWithInitAttribute:
        def __init__(self) -> None:
            self.nested = Nested()

    for klass in (OuterWithProperty, OuterWithClassAttribute, OuterWithInitAttribute):

        with subtests.test(klass.__name__):
            obj = OuterWithProperty()
            for method, expected_args in (
                (Nested.instancemethod_foo, (obj.nested,)),
                (Nested.classmethod_foo, (Nested,)),
                (Nested.staticmethod_foo, tuple()),
            ):
                with subtests.test(method.__name__):

                    unbound_cmd = UnboundCommand.from_callable(method.__name__.replace("_", "-"), method).for_namespace(
                        "nested"
                    )
                    assert unbound_cmd.parent_namespaces == ("nested",)
                    cmd = unbound_cmd.bind(obj)
                    assert cmd.func == getattr(obj.nested, method.__name__)
                    cmd.func()

                    method_mock.assert_called_once_with(*expected_args)
                    method_mock.reset_mock()


def test_command():
    def foo():
        ...


def test_unbound_command_bind_nested_module(subtests):
    def foo():
        ...

    with subtests.test("function"):
        UnboundCommand.from_callable("foo", foo)
