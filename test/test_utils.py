import itertools

from argparse_shell import decorators, utils


def test_split_to_literals(subtests):
    """Test splitting a string into multiple Python literals"""
    ints = range(2)
    floats = [_ + 0.2 for _ in range(2)]
    strs = ["test" for _ in range(2)]
    strs_with_spaces = [f"test {_}" for _ in range(2)]

    base_sequences = (ints, floats, strs, strs_with_spaces)
    sequence_types = (list, tuple, set)

    items = (
        "test",
        "'with spaces'",
        *[sequence_type(sequence) for sequence_type, sequence in itertools.product(sequence_types, base_sequences)],
    )

    for item in items:
        with subtests.test(item=item):
            literals = list(utils.split_to_literals(str(item)))
            assert literals == [str(item)]

    nested_dicts = [dict(inner=dict(foo=item)) for item in items]
    for item in nested_dicts:
        with subtests.test(item=item):
            literals = list(utils.split_to_literals(str(item)))
            assert literals == [str(item)]

    nested_sequences = [sequence.__class__([sequence]) for sequence in items if not isinstance(sequence, (str, set))]
    for item in nested_sequences:

        with subtests.test(item=item):
            literals = list(utils.split_to_literals(str(item)))
            assert literals == [str(item)]

    with subtests.test(msg="all combined"):
        all_items = list(str(item) for item in itertools.chain(items, nested_dicts, nested_sequences))
        literals = list(utils.split_to_literals(" ".join(all_items)))
        assert literals == all_items


def test_find_nth():
    """Test the function to find the nth occurrence of a substring"""
    word = "test"

    input_data = word * 10
    assert utils.find_nth(input_data, "e", 0) == 1
    assert utils.find_nth(input_data, "e", 1) == len(word) + 1
    assert utils.find_nth(input_data, "e", 2) == 2 * len(word) + 1
    assert utils.find_nth(input_data, "e", 1, start=3) == 2 * len(word) + 1

    # Only one occurrence for 'e' in 'test'
    assert utils.find_nth(word, "e", 1) == -1

    assert utils.find_nth(word, "t", 1, end=-1) == -1


def test_parse_arg_string():
    """Test parsing of argument strings for the interactive shell"""
    args = (1, 2, "test")
    kwargs = dict(something="else", something2=["test", 1.5], subd=dict())
    args_string_items = [str(arg) for arg in args]
    kwargs_string_items = [f"{key}={value}" for key, value in kwargs.items()]
    assert utils.parse_arg_string(" ".join(args_string_items)) == (args, dict())
    assert utils.parse_arg_string(" ".join(kwargs_string_items)) == (tuple(), kwargs)

    assert utils.parse_arg_string(
        " ".join(f"{arg} {kwarg}" for arg, kwarg in zip(args_string_items, kwargs_string_items))
    ) == (args, kwargs)


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
