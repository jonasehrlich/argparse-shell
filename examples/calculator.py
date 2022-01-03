#! /usr/bin/env python3
from argparse_shell import ArgparseShell


class Calculator:
    """A simple calculator example"""

    def add(self, a: float, b: float) -> float:
        """Add two numbers

        :param a: First number
        :param b: Second number
        :return: Sum of two numbers
        """
        return a + b

    def div(self, a: float, b: float) -> float:
        """
        Divide numbers

        :param a: First number
        :param b: Second number
        :return: Division of two numbers"""
        return a / b

    def mult(self, a: float, b: float) -> float:
        """Multiply two numbers

        :param a: First number
        :param b: Second number
        :return: Product of two numbers
        """
        return a * b

    def sub(self, a: float, b: float) -> float:
        """Substract two numbers

        :param a: First number
        :type a: float
        :param b: Second number
        :type b: float
        :return: Substraction of the two numbers
        :rtype: float
        """
        return a - b


if __name__ == "__main__":
    calc = Calculator()
    shell = ArgparseShell.from_object(calc, program_name="calc")
    shell.main()
