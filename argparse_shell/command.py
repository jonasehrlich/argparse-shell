from __future__ import annotations

import enum
import functools
import inspect
import textwrap
import typing as ty

import docstring_parser

from . import utils, wrappers

__all__ = ["UnsupportedCommandTypeError", "Command", "UnboundCommand"]

CT = ty.TypeVar("CT")
CommandBase_T = ty.TypeVar("CommandBase_T", bound="_CommandBase")
UnboundCommand_T = ty.TypeVar("UnboundCommand_T", bound="UnboundCommand")

InteractiveHelpMethod = ty.Callable[[], None]
InteractiveCommandMethod = ty.Callable[[str], None]


class UnsupportedCommandTypeError(Exception):
    """Raised if a command should be created from an unsupported type"""


class _CommandBase:
    """Base class for commands. This class implements the basic methods to get metadata on the function the command
    implements"""

    _INTERACTIVE_METHOD_PREFIX = "do_"
    _INTERACTIVE_HELP_METHOD_PREFIX = "help_"

    def __init__(self, name: str, func: ty.Callable) -> None:
        self.name = name
        self.func = func

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({repr(self.func)})"

    def __call__(self, *args: ty.Any, **kwargs: ty.Any) -> ty.Any:
        return self.func(*args, **kwargs)

    def signature(self) -> inspect.Signature:
        """Get the signature of the command"""
        return inspect.signature(self.func)

    def docstring(self) -> str:
        """Return a valid docstring for any object"""
        return textwrap.dedent(
            (inspect.getdoc(self.func) or f"{self.func.__name__} {self.func.__class__.__name__}").strip()
        )

    def description(self) -> str:
        """Return the description that is parsed from the docstring"""
        parse_result = docstring_parser.parse(self.docstring())

        description_components = []
        if parse_result.short_description:
            description_components.append(parse_result.short_description)
        if parse_result.long_description:
            description_components.append(parse_result.long_description)
        return "\n\n".join(description_components)

    def _pythonize_name(self) -> str:
        """Create a Python name from the command name"""
        return self.name.replace("-", "_")

    @property
    def interactive_method_name(self) -> str:
        """Get the name for the interactive method for this command"""
        return f"{self._INTERACTIVE_METHOD_PREFIX}{self.name}"

    @property
    def interactive_help_method_name(self) -> str:
        """Get the name for the interactive help method for this command"""
        return f"{self._INTERACTIVE_HELP_METHOD_PREFIX}{self.name}"


class WrappedCommandType(enum.Enum):
    """Type of the command that is wrapped"""

    FUNCTION = enum.auto()
    METHOD = enum.auto()
    GENERATOR = enum.auto()
    ASYNCGENERATOR = enum.auto()
    DATADESCRIPTOR = enum.auto()
    COROUTINEFUNCTION = enum.auto()


class UnboundCommand(_CommandBase):
    def __init__(
        self,
        name: str,
        func: ty.Callable,
        wrapped_command_type: WrappedCommandType,
        parent_namespaces: ty.Sequence[str] = tuple(),
    ) -> None:
        super().__init__(name, func)
        self.parent_namespaces: ty.Tuple[str, ...] = tuple(parent_namespaces)
        self._wrapped_command_type = wrapped_command_type

    @classmethod
    def from_callable(cls: ty.Type[UnboundCommand_T], name: str, func: ty.Callable) -> UnboundCommand_T:
        """Create an unbound command from an arbitrary object

        :param cls: Class that is created
        :type cls: ty.Type[UnboundCommand]
        :param name: Name of the command
        :type name: str
        :param func: Callable that implements the command
        :type func: ty.Callable
        :raises UnsupportedCommandTypeError: Raised if the type of the callable is not supported
        :return: Unbound command wrapping the callable
        :rtype: T
        """
        if inspect.isdatadescriptor(func):
            wrapped = wrappers.wrap_datadescriptor(func)
            cmd_type = WrappedCommandType.DATADESCRIPTOR
        elif inspect.iscoroutinefunction(func):
            wrapped = wrappers.wrap_corofunc(func)
            cmd_type = WrappedCommandType.COROUTINEFUNCTION
        elif inspect.ismethod(func):
            wrapped = func
            cmd_type = WrappedCommandType.METHOD
        elif inspect.isfunction(func):
            wrapped = func
            cmd_type = WrappedCommandType.FUNCTION
        else:
            raise UnsupportedCommandTypeError(f"{func.__class__.__name__} is not a supported command type")
        return cls(name, wrapped, cmd_type)

    def for_namespace(self: UnboundCommand_T, namespace_name: str) -> UnboundCommand_T:
        """Create a new command object for a namespace.

        :param namespace_name: Namespace the new command should be located in
        :type namespace_name: str
        :return: New command with an updated namespace chain
        :rtype: UnboundCommand_T
        """
        namespace_prefix = utils.python_name_to_dashed(namespace_name)

        return self.__class__(
            f"{namespace_prefix}-{self.name}",
            self.func,
            self._wrapped_command_type,
            (namespace_name,) + self.parent_namespaces,
        )

    def bind(self, obj: ty.Any) -> Command:
        """
        Bind the command to any object if it is an unbound method. If `obj` is a module, the callable is
        already a method or `obj` is explicitly set to None, no binding will happen

        :param obj: Object to bind to, if this is explicitly set to None, no binding will happen
        :type obj: ty.Any
        """
        # TODO: Eventually move resolution of parent namespaces to runtime
        for namespace in self.parent_namespaces:
            # Step through the parent namespaces to get to the object the command should be bound to
            obj = getattr(obj, namespace)

        if inspect.ismodule(obj) or inspect.ismethod(self.func) or obj is None:
            # Callables cannot be bound to modules
            # The method is already bound, there's nothing to do anymore
            return Command(self.name, self.func)

        if self._wrapped_command_type == WrappedCommandType.DATADESCRIPTOR:
            _func = functools.partial(self.func, obj)
        else:
            _func = getattr(obj, self.func.__name__)
        return Command(self.name, _func)

    def signature(self) -> inspect.Signature:
        """Get the signature of the command"""
        sig = super().signature()

        updated_parameters = list(sig.parameters.values())
        if len(updated_parameters) and updated_parameters[0].name == "self":
            # We have a method that is unbound, remove the instance parameter from the signature
            sig = sig.replace(parameters=updated_parameters[1:])

        return sig


class Command(_CommandBase):
    """
    Command class wrapping the function that executes the command, should be created by creating an
    :py:class:`UnboundCommand` and binding it to an object
    """

    def __init__(self, name: str, func: ty.Callable) -> None:
        super().__init__(name, func)
        self._interactive_method = None
        self._interactive_help_method = None

    @property
    def interactive_help_method(self) -> InteractiveHelpMethod:
        """Get the interactive help method to be called by the interactive shell"""
        if self._interactive_help_method is None:
            self._interactive_help_method = self._get_interactive_help_method()
        return self._interactive_help_method

    @property
    def interactive_method(self) -> InteractiveCommandMethod:
        if self._interactive_method is None:
            self._interactive_method = self._get_interactive_method()
        return self._interactive_method

    @ty.overload
    def get_interactive_method_for_prefix(self, prefix: ty.Literal["help_"]) -> InteractiveHelpMethod:
        ...

    @ty.overload
    def get_interactive_method_for_prefix(self, prefix: ty.Literal["do_"]) -> InteractiveCommandMethod:
        ...

    def get_interactive_method_for_prefix(
        self, prefix: str
    ) -> ty.Union[InteractiveCommandMethod, InteractiveHelpMethod]:
        """Get the interactive method for a prefix.

        This method returns either the :py:attr:`Command.interactive_method` or the
        :py:attr:`Command.interactive_help_method` depending on the prefix value

        :param prefix: Prefix string of the command
        :type prefix: str
        :raises ValueError: Raised if the prefix is unknown
        :return: Interactive method for a prefix for this command
        :rtype: ty.Union[InteractiveCommandMethod, InteractiveHelpMethod]
        """
        if prefix == self._INTERACTIVE_METHOD_PREFIX:
            return self.interactive_method
        if prefix == self._INTERACTIVE_HELP_METHOD_PREFIX:
            return self.interactive_help_method
        raise ValueError(f"Unknown prefix '{prefix}'")

    def _get_interactive_help_method(self) -> ty.Callable[[], None]:
        """Creates a help function to use in the interactive mode

        :param func: Function to create the help function for
        :type func: ty.Callable
        """
        parse_result = docstring_parser.parse(self.docstring())
        command_description = self.description()
        sig = self.signature()

        # Get a mapping of parameters defined in the docstring
        docstring_params = {param.arg_name: param for param in parse_result.params}

        usage_str = f"usage: {self.name} "

        # Build parameters section for the help of this command
        params_section_list = list()

        for param_name, param in sig.parameters.items():
            docstring_param = docstring_params.get(param_name)
            if docstring_param:
                # Default to the description of the parameter in the docstring
                param_description = docstring_param.description
            else:
                # If we don't have a docstring of the parameter, use the kind as a description
                param_description = param.kind.name.lower().replace("_", " ")
            params_section_list.append(f"  {param}\t{param_description}")
            usage_str += f"{param_name} "

        if params_section_list:
            # Insert the heading 'Parameters:' in case we have parameters
            params_section_list.insert(0, "Parameters:")

        # Build the returns section of the help of this command
        returns_section_list = list()
        returns_section_list.append("Returns:")

        return_annotation = ty.Any if sig.return_annotation is sig.empty else sig.return_annotation
        return_description = parse_result.returns.description if parse_result.returns else ""

        returns_section_list.append(f"  {inspect.formatannotation(return_annotation)}: {return_description}")

        parameters_section = "\n".join(params_section_list)
        returns_section = "\n".join(returns_section_list)
        help_text = f"{usage_str}\n\n{command_description}\n\n{parameters_section}\n\n{returns_section}\n"

        def do_help():
            print(help_text)

        do_help.__name__ = f"help_{self.func.__name__}"
        return do_help

    def _get_interactive_method(self) -> ty.Callable[[str], None]:
        """Get the method wrapped for an interactive shell"""
        return wrappers.wrap_interactive_method(wrappers.pprint_wrapper(self.func))
