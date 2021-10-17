import pytest
from argparse_shell.namespace import Namespace, UnboundNamespace


def test_unbound_namespace_from_object_getter_property(subtests):
    """Test namespace building for objects with a getter property"""

    class Driver:
        @property
        def name(self) -> str:
            return "test"

    with subtests.test("object"):
        namespace = UnboundNamespace.from_object(Driver())
        assert list(namespace.keys()) == ["name"]

    with subtests.test("class"):
        namespace = UnboundNamespace.from_object(Driver)
        assert list(namespace.keys()) == ["name"]


def test_unbound_namespace_from_object_getter_setter_property(subtests):
    """Test namespace building for objects with a getter / setter property"""

    class Driver:
        @property
        def name(self) -> str:
            return "test"

        @name.setter
        def name(self, value: str):
            ...

    with subtests.test("object"):
        namespace = UnboundNamespace.from_object(Driver())
        assert list(namespace.keys()) == ["name"]

    with subtests.test("class"):
        namespace = UnboundNamespace.from_object(Driver)
        assert list(namespace.keys()) == ["name"]


def test_unbound_namespace_from_object_coroutine(subtests):
    """Test namespace building for objects with a getter / setter property"""

    class Driver:
        async def my_coro(self):
            ...

    with subtests.test("object"):
        namespace = UnboundNamespace.from_object(Driver())
        assert list(namespace.keys()) == ["my-coro"]

    with subtests.test("class"):
        namespace = UnboundNamespace.from_object(Driver)
        assert list(namespace.keys()) == ["my-coro"]


def test_unbound_namespace_from_object_method(subtests):
    """Test namespace building for objects with methods"""

    class Driver:
        def my_method(self):
            ...

    with subtests.test("object"):
        namespace = UnboundNamespace.from_object(Driver())
        assert list(namespace.keys()) == ["my-method"]

    with subtests.test("class"):
        namespace = UnboundNamespace.from_object(Driver)
        assert list(namespace.keys()) == ["my-method"]


def test_unbound_namespace_from_object_classmethod(subtests):
    """Test namespace building for objects with methods"""

    class Driver:
        @classmethod
        def my_method(cls):
            ...

    with subtests.test("object"):
        namespace = UnboundNamespace.from_object(Driver())
        assert list(namespace.keys()) == ["my-method"]

    with subtests.test("class"):
        namespace = UnboundNamespace.from_object(Driver)
        assert list(namespace.keys()) == ["my-method"]


def test_unbound_namespace_from_object_staticmethod(subtests):
    """Test namespace building for objects with methods"""

    class Driver:
        @staticmethod
        def my_method():
            ...

    with subtests.test("object"):
        namespace = UnboundNamespace.from_object(Driver())
        assert list(namespace.keys()) == ["my-method"]

    with subtests.test("class"):
        namespace = UnboundNamespace.from_object(Driver)
        assert list(namespace.keys()) == ["my-method"]


def test_unbound_namespace_from_object_private_method(subtests):
    """Test namespace building for objects with methods"""

    class Driver:
        def _my_method(self):
            ...

    with subtests.test("object"):
        namespace = UnboundNamespace.from_object(Driver())
        assert not namespace

    with subtests.test("class"):
        namespace = UnboundNamespace.from_object(Driver)
        assert not namespace


def test_unbound_namespace_from_object_other_attribute(subtests):
    """Test normal attributes are not included in the namespace"""

    class Driver:
        def __init__(self) -> None:
            self.name = 10

    with subtests.test("object"):
        namespace = UnboundNamespace.from_object(Driver())
        assert not namespace

    with subtests.test("class"):
        namespace = UnboundNamespace.from_object(Driver)
        assert not namespace


def test_namespace_from_object_getter_property():
    """Test namespace building for objects with a getter property"""

    class Driver:
        @property
        def name(self) -> str:
            return "test"

    namespace = Namespace.from_object(Driver())
    assert list(namespace.keys()) == ["name"]


def test_namespace_from_object_getter_setter_property():
    """Test namespace building for objects with a getter / setter property"""

    class Driver:
        @property
        def name(self) -> str:
            return "test"

        @name.setter
        def name(self, value: str):
            ...

    namespace = Namespace.from_object(Driver())
    assert list(namespace.keys()) == ["name"]


def test_namespace_from_object_coroutine():
    """Test namespace building for objects with a getter / setter property"""

    class Driver:
        async def my_coro(self):
            ...

    namespace = Namespace.from_object(Driver())
    assert list(namespace.keys()) == ["my-coro"]


def test_namespace_from_object_method():
    """Test namespace building for objects with methods"""

    class Driver:
        def my_method(self):
            ...

    namespace = Namespace.from_object(Driver())
    assert list(namespace.keys()) == ["my-method"]


def test_namespace_from_object_private_method():
    """Test namespace building for objects with methods"""

    class Driver:
        def _my_method(self):
            ...

    namespace = Namespace.from_object(Driver())
    assert not namespace


def test_namespace_from_object_other_attribute():
    """Test normal attributes are not included in the namespace"""

    class Driver:
        def __init__(self) -> None:
            self.name = 10

    namespace = Namespace.from_object(Driver())
    assert not namespace


def test_unbound_nested_namespace_class(subtests):
    """Test namespace building if nesting is through a class or instance"""

    class Nested:
        def foo(self):
            ...

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

    with subtests.test("class nesting in property"):
        nested_namespace = UnboundNamespace.from_object(Nested)
        namespace = UnboundNamespace.from_object(OuterWithProperty, nested_namespaces=dict(nested=nested_namespace))

        assert list(namespace.keys()) == ["nested-foo"]
        assert namespace["nested-foo"].parent_namespaces == ("nested",)

    with subtests.test("class nesting in class attribute"):
        nested_namespace = UnboundNamespace.from_object(Nested)
        namespace = UnboundNamespace.from_object(
            OuterWithClassAttribute, nested_namespaces=dict(nested=nested_namespace)
        )

        assert list(namespace.keys()) == ["nested-foo"]
        assert namespace["nested-foo"].parent_namespaces == ("nested",)

    with subtests.test("class nesting in init attribute"):
        nested_namespace = UnboundNamespace.from_object(Nested)
        with pytest.raises(RuntimeError):
            namespace = UnboundNamespace.from_object(
                OuterWithInitAttribute, nested_namespaces=dict(nested=nested_namespace)
            )

    with subtests.test("instance nesting in init attribute"):
        nested_namespace = UnboundNamespace.from_object(Nested)
        namespace = UnboundNamespace.from_object(
            OuterWithInitAttribute(), nested_namespaces=dict(nested=nested_namespace)
        )
        assert list(namespace.keys()) == ["nested-foo"]
        assert namespace["nested-foo"].parent_namespaces == ("nested",)


def test_unbound_nested_namespace_module():
    ...
