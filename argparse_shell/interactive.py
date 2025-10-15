import typing as ty
from cmd import Cmd

from argparse_shell.namespace import Namespace


class InteractiveCmd(Cmd):
    """Subclass of the base :py:class:`cmd.Cmd`.

    This class wraps a :py:class:`~argparse_shell.namespace.Namespace` and makes its commands available in an
    interactive shell.
    """

    _CMD_IMPLEMENTATION_PREFIX = "do_"
    _HELP_IMPLEMENTATION_PREFIX = "help_"
    identchars = Cmd.identchars + "-"

    def __init__(self, namespace: Namespace, stop_on_eof: bool = True, *args, **kwargs) -> None:
        """Initialize an interactive shell working with a namespace instead of subclassing.

        The interactive shell will use all commands consisting of multiple words as dashes.

        :param namespace: Definition of a namespace containing commands to
        :type namespace: Namespace
        :param stop_on_eof: Whether to stop when a EOF (Ctrl + D) is received, defaults to True
        :type stop_on_eof: bool, optional
        """
        super().__init__(*args, **kwargs)

        self._namespace = namespace
        if stop_on_eof:

            def do_eof(_):
                self.stdout.write("EOF: exit\n")
                return True

            self.do_EOF = do_eof

    def preloop(self) -> None:
        """Pre loop hook. Remove dashes from the word delimiters in the `readline` module"""
        try:
            import readline  # noqa: PLC0415

            # Remove dashes from the readline auto completion delimiters
            readline.set_completer_delims(readline.get_completer_delims().replace("-", ""))
        except ImportError:
            pass

    def get_names(self) -> ty.List[str]:
        """
        Get a list of all command and help method implementations in the namespace nested in this class
        """
        names = list()
        for cmd in self._namespace.values():
            names.append(cmd.interactive_method_name)
            names.append(cmd.interactive_help_method_name)
        return names

    def __getattr__(self, name: str):
        """Fallback for attribute accesses, to replace dashes with underscores"""
        for prefix in (self._CMD_IMPLEMENTATION_PREFIX, self._HELP_IMPLEMENTATION_PREFIX):
            if name.startswith(prefix):
                try:
                    prefix_len = len(prefix)
                    cmd = self._namespace[name[prefix_len:]]
                    return cmd.get_interactive_method_for_prefix(prefix, self.stdout)
                except (KeyError, ValueError) as exc:
                    raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'") from exc

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def emptyline(self) -> bool:
        # We don't want to execute the last command if nothing was typed
        return False
