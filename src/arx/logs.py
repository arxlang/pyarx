import sys
from typing import Optional, TypeVar


def LogError(message: str):
    """
    LogError - A helper function for error handling.

    Parameters
    ----------
    message : str
        The error message.

    Returns
    -------
    None
        Returns None as an error indicator.
    """
    print(f"Error: {message}\n", file=sys.stderr)


LogErrorV = LogError
