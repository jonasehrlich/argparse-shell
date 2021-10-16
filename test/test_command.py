from argparse_shell.command import Command, UnboundCommand


def test_command_get_docstring():
    """Test creation of docstrings from existing methods"""

    def no_docstring():
        ...

    assert UnboundCommand("test", no_docstring).docstring() == "no_docstring function"

    expected_docstring = "Hello this is a docstring\nwhich should get dedented"

    def with_docstring():
        """Hello this is a docstring
        which should get dedented"""

    assert UnboundCommand("Test", with_docstring).docstring() == expected_docstring

    def with_docstring2():
        """
        Hello this is a docstring
        which should get dedented
        """

    assert UnboundCommand("Test", with_docstring2).docstring() == expected_docstring
