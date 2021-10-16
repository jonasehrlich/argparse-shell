from __future__ import annotations

import collections
import inspect
import typing as ty

from . import utils
from .command import Command, UnsupportedCommandTypeError, UnboundCommand

T = ty.TypeVar("T")
Command_T = ty.TypeVar("Command_T")


class _NamespaceBase(collections.UserDict, ty.Dict[str, Command_T]):
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({super().__repr__()})"


class Namespace(_NamespaceBase[Command]):
    @classmethod
    def from_object(cls: ty.Type[T], obj: ty.Any) -> T:
        """Build a namespace from an object. The namespace is a mapping of command names to callback functions.
        This layer wraps coroutine functions and descriptors in functions, to allow them being called directly.

        :param obj: Object to build the namespace from
        :type obj: ty.Any
        :return: Mapping of command names defined in an object
        :rtype: Namespace
        """
        unbound_namespace = UnboundNamespace.from_object(obj)
        return unbound_namespace.bind(obj, cls)


class UnboundNamespace(_NamespaceBase[UnboundCommand]):
    def bind(self, obj: ty.Any, namespace_cls: ty.Type[T] = Namespace) -> T:
        namespace = namespace_cls()
        for cmd in self.values():
            namespace[cmd.name] = cmd.bind(obj)
        return namespace

    @classmethod
    def from_object(cls: ty.Type[T], obj: ty.Any) -> T:
        """Build a namespace from an object. The namespace is a mapping of command names to callback functions.
        This layer wraps coroutine functions and descriptors in functions, to allow them being called directly.

        :param obj: Object to build the namespace from
        :type obj: ty.Any
        :return: Mapping of command names defined in an object
        :rtype: Namespace
        """
        namespace = cls()

        if inspect.isclass(obj) or inspect.ismodule(obj):
            detect_obj = obj
        else:
            # Use the class of arbitrary objects to build a namespace
            detect_obj = obj.__class__

        for name, value in inspect.getmembers(detect_obj):
            if not utils.is_shell_cmd(value, name):
                continue

            cmd_name = utils.get_command_name(value, name)
            try:
                namespace[cmd_name] = UnboundCommand.from_callable(cmd_name, value)
            except UnsupportedCommandTypeError:
                pass

        return namespace
