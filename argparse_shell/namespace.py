from __future__ import annotations

import collections
import inspect
import typing as ty

from . import utils
from .command import Command, UnsupportedCommandTypeError, UnboundCommand


T = ty.TypeVar("T")
Command_T = ty.TypeVar("Command_T")


class DuplicateCommandNameError(KeyError):
    """Raised if a command name is added for a second time to a namespace"""


class _NamespaceBase(collections.UserDict, ty.Dict[str, Command_T]):
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__repr__()})"

    def __setitem__(self, key: str, item: Command_T) -> None:
        if key in self:
            raise DuplicateCommandNameError(f"Command '{key}' is already defined in namespace")
        return super().__setitem__(key, item)


class Namespace(_NamespaceBase[Command]):
    @classmethod
    def from_object(
        cls: ty.Type[T], obj: ty.Any, nested_namespaces: ty.Optional[ty.Mapping[str, UnboundNamespace]] = None
    ) -> T:
        """Build a namespace from an object. The namespace is a mapping of command names to callback functions.
        This layer wraps coroutine functions and descriptors in functions, to allow them being called directly.

        :param obj: Object to build the namespace from
        :type obj: ty.Any
        :param nested_namespaces: Mappin
        :return: Mapping of command names defined in an object
        :rtype: Namespace
        """
        unbound_namespace = UnboundNamespace.from_object(obj, nested_namespaces=nested_namespaces)
        return unbound_namespace.bind(obj, cls)


class UnboundNamespace(_NamespaceBase[UnboundCommand]):
    def bind(self, obj: ty.Any, namespace_cls: ty.Type[T] = Namespace) -> T:
        namespace = namespace_cls()
        for cmd in self.values():
            namespace[cmd.name] = cmd.bind(obj)
        return namespace

    @classmethod
    def from_object(  # noqa: C901
        cls: ty.Type[T], obj: ty.Any, nested_namespaces: ty.Optional[ty.Mapping[str, UnboundNamespace]] = None
    ) -> T:
        """Build a namespace from an object. The namespace is a mapping of command names to callback functions.
        This layer wraps coroutine functions and descriptors in functions, to allow them being called directly.

        :param obj: Object to build the namespace from
        :type obj: ty.Any
        :param nested_namespaces: Mapping of namespace names to unbound, nested namespaces, defaults to None
        :type nested_namespaces: ty.Mapping[str, UnboundNamespace], optional
        :return: Mapping of command names defined in a namespace to :py:class:`UnboundCommand` objects
        :rtype: UnboundNamespace
        """
        namespace = cls()
        nested_namespaces = dict(nested_namespaces) if nested_namespaces else dict()

        if inspect.isclass(obj) or inspect.ismodule(obj):
            detect_obj = obj
            is_instance = False
        else:
            # Use the class of arbitrary objects to build a namespace
            detect_obj = obj.__class__
            is_instance = True

        for name, value in inspect.getmembers(detect_obj):
            if not utils.is_shell_cmd(value, name):
                continue

            nested_namespace = nested_namespaces.pop(name, None)
            if nested_namespace:
                for cmd_name, value in nested_namespace.items():
                    namespace_cmd = value.for_namespace(name)
                    namespace[namespace_cmd.name] = namespace_cmd
                continue

            cmd_name = utils.get_command_name(value, name)
            try:
                namespace[cmd_name] = UnboundCommand.from_callable(cmd_name, value)
            except UnsupportedCommandTypeError:
                pass

        if nested_namespaces and is_instance:
            # We have still nested namespaces left and the object argument was not a class or a module,
            # check if the namespaces exist in the object and were defined during initialization
            nested_namespaces_copy = dict(nested_namespaces)
            instance_attributes = set(dir(obj))
            for name, nested_namespace in nested_namespaces_copy.items():
                if name in instance_attributes:
                    for cmd_name, value in nested_namespace.items():
                        namespace_cmd = value.for_namespace(name)
                        namespace[namespace_cmd.name] = value.for_namespace(name)
                    nested_namespaces.pop(name, None)

        if nested_namespaces:
            # Nested namespaces were defined but could not be found, raise a RuntimeError
            raise RuntimeError(
                f"Defined nested namespaces: {list(nested_namespaces)} could not be found in object {obj!r}"
            )
        return namespace
