"""The logs functions and classes handle all the system messages."""

import sys


def LogError(message: str) -> None:
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
