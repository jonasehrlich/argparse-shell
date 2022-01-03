import functools
import io
import typing as ty
from unittest import mock
import sys
from argparse_shell import ArgparseShell

__all__ = ["ArgparseShellRunner", "Result", "PostcmdLoopStopError"]


class PostcmdLoopStopError(Exception):
    """Raised if the :py:meth:`Cmd.postcmd` method returned True"""


class Result:
    def __init__(self, output: str, stopped: bool, error: ty.Optional[Exception]) -> None:
        self.stopped = stopped
        self.output = output
        self.error: ty.Optional[Exception] = error

    def check(self) -> None:
        """Check that the interactive command was executed as expected, and no stop was indicated by"""
        if self.error:
            raise self.error
        if self.stopped:
            raise PostcmdLoopStopError("The postcmd returned a stop")


class ArgparseShellRunner:
    def __init__(self, argparse_shell: ArgparseShell) -> None:
        self.argparse_shell = argparse_shell

    @staticmethod
    def _format_interactive_cmd(cmd: str, *args) -> str:
        """Format a command and args to an interactive command"""
        arg_str = " ".join(str(arg) for arg in args)
        return f"{cmd} {arg_str}\n"

    def invoke_interactive(self, cmd: str, *args: ty.Any, strip_prompt: bool = True) -> Result:
        # bytes_output = io.BytesIO()
        # stdout = io.TextIOWrapper(bytes_output)

        # old_stdout = self.argparse_shell.interactive.stdout
        # self.argparse_shell.interactive.stdout = stdout

        self.argparse_shell.interactive.cmdqueue = [self._format_interactive_cmd(cmd, *args)]
        stopped = False
        error = None
        try:
            with mock.patch.object(
                self.argparse_shell.interactive,
                "postcmd",
                wraps=self._get_postcmd_wrapper(self.argparse_shell.interactive.postcmd),
            ):
                self.argparse_shell.main([])
        except PostcmdLoopStopError:
            stopped = True
            self.argparse_shell.interactive.postloop()
        except Exception as exc:
            error = exc

        # Seek position to 0 in order to be able to directly read stdin and stdout
        self.argparse_shell.interactive.stdout.seek(0)
        output = self.argparse_shell.interactive.stdout.read()
        if strip_prompt and output.startswith(self.argparse_shell.interactive.prompt):
            prompt_len = len(self.argparse_shell.interactive.prompt)
            output = output[prompt_len:]
        return Result(output, stopped, error)

    def _get_postcmd_wrapper(self, postcmd: ty.Callable[[bool, str], bool]) -> ty.Callable:
        """Get a wrapper for the postcmd method of the internal Cmd object"""

        @functools.wraps(postcmd)
        def wrapper(*args, **kwargs):

            stop = postcmd(*args, **kwargs)
            # If stop is true, the loop should be ended. This is unexpected behavior, so raise the error.
            if stop:
                raise PostcmdLoopStopError()
            # Return True to end the cmdloop
            return True

        return wrapper
