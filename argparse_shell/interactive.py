import cmd
import typing as ty


class InteractiveCmd(cmd.Cmd):
    """Subclass of the base :py:class:`cmd.Cmd`.

    This subclass makes the commands default to use dashes instead of underscores. This is done by doing three changes:

    * Remove the dash from the word delimiters in the readline module
    """

    _CMD_IMPLEMENTATION_PREFIX = "do_"
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
        Overwritten get_names function to change the underscores in the command implementation function
        names to dashes.

        :return: List of members of this class
        :rtype: ty.List[str]
        """
        names = list()
        for name in super().get_names():
            if name.startswith(self._CMD_IMPLEMENTATION_PREFIX):
                names.append(f"{self._CMD_IMPLEMENTATION_PREFIX}{name[3:].replace('_', '-')}")
            else:
                names.append(name)
        return names

    def __getattr__(self, name: str):
        """Fallback for attribute accesses, to replace dashes with underscores"""
        if "-" in name:
            return getattr(self, name.replace("-", "_"))
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
