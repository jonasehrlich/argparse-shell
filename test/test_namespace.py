from argparse_shell.namespace import UnboundNamespace, Namespace


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
