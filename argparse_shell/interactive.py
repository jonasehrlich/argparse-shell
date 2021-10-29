import cmd
import typing as ty

from . import utils


class InteractiveCmd(cmd.Cmd):
    """Subclass of the base :py:class:`cmd.Cmd`.

    This subclass makes the commands default to use dashes instead of underscores. This is done by doing three changes:

    * Remove the dash from the word delimiters in the readline module
    """

    _CMD_IMPLEMENTATION_PREFIX = "do_"
    _HELP_IMPLEMENTATION_PREFIX = "help_"
    identchars = cmd.Cmd.identchars + "-"

    def preloop(self) -> None:
        """Pre loop hook. Remove dashes from the word delimiters in the `readline` module"""
        try:
            import readline  # pylint: disable=import-outside-toplevel

            # Remove dashes from the readline auto completion delimiters
            readline.set_completer_delims(readline.get_completer_delims().replace("-", ""))
        except ImportError:
            pass

    def get_names(self) -> ty.List[str]:
        """
        Overwritten get_names method to change the underscores in the command and help implementation method
        names to dashes.

        :return: List of members of this class
        :rtype: ty.List[str]
        """
        names = list()
        for name in super().get_names():
            for prefix in (self._CMD_IMPLEMENTATION_PREFIX, self._HELP_IMPLEMENTATION_PREFIX):
                if name.startswith(prefix):
                    names.append(f"{prefix}{utils.python_name_to_dashed(name[len(prefix):])}")
                    break
            else:
                names.append(name)
        return names

    def __getattr__(self, name: str):
        """Fallback for attribute accesses, to replace dashes with underscores"""
        if "-" in name:
            return getattr(self, name.replace("-", "_"))
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def emptyline(self) -> bool:
        # We don't want to execute the last command if nothing was typed
        return False
