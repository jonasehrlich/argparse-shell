from argparse_shell import decorators, utils


def test_eval_literal_value():
    """Test evaluation of literals"""
    str_value = "test"
    assert utils.eval_literal_value(str_value) == str_value

    assert utils.eval_literal_value(f"'{str_value}'") == str_value
    int_value = 123
    for representation in (str, hex, bin, oct):
        assert utils.eval_literal_value(representation(int_value)) == int_value

    float_value = 1.234
    assert utils.eval_literal_value(str(float_value)) == float_value


def test_is_shell_cmd():
    """Test detection of shell commands"""

    def valid_command():
        ...

    def _private_command():
        ...

    assert utils.is_shell_cmd(valid_command) is True
    assert utils.is_shell_cmd(decorators.no_shell_cmd(valid_command)) is False
    assert utils.is_shell_cmd(_private_command) is False


def test_get_command_name():
    """Test command name creation"""
    names = (
        ("CamelCase", "camel-case"),
        ("CamelCase1", "camel-case1"),
        ("snake_case", "snake-case"),
        ("snake_1", "snake-1"),
        ("MixedCamel_snake", "mixed-camel-snake"),
    )

    for input_name, expected_name in names:
        def func():
            ...

        func.__name__ = input_name
        assert utils.get_command_name(func) == expected_name

    cmd_name = "my_cmd"
    @decorators.command(cmd_name)
    def func2():
        ...
    assert utils.get_command_name(func2) == cmd_name


def test_get_docstring():
    """Test creation of docstrings from existing methods"""

    def no_docstring():
        ...

    assert utils.get_docstring(no_docstring) == "no_docstring function"

    expected_docstring = "Hello this is a docstring\nwhich should get dedented"

    def with_docstring():
        """Hello this is a docstring
        which should get dedented"""

    assert utils.get_docstring(with_docstring) == expected_docstring

    def with_docstring2():
        """
        Hello this is a docstring
        which should get dedented
        """

    assert utils.get_docstring(with_docstring2) == expected_docstring
