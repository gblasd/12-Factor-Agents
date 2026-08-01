def sum_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

def subtract_numbers(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b

def divide_numbers(a: float, b: float) -> float:
    """Divide a by b. Raises ValueError if b is zero."""
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return base ** exponent

def square_root(x: float) -> float:
    """Calculate the square root of x. Raises ValueError if x is negative."""
    if x < 0:
        raise ValueError("Square root of negative number")
    return x ** 0.5