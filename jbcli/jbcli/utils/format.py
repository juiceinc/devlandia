"""Provides standardized methods and colors for various console message
outputs.
"""
from click import secho


def echo_highlight(message):
    """Uses click to produce an highlighted (yellow) console message

    :param message: The message to be echoed in the highlight color
    :type message: str
    """
    return secho(message, fg='yellow', bold=True)


def echo_warning(message):
    """Uses click to produce an warning (red) console message

    :param message: The message to be echoed in the warning color
    :type message: str
    """
    return secho(message, fg='red', bold=True)


def echo_success(message):
    """Uses click to produce an success (green) console message

    :param message: The message to be echoed in the success color
    :type message: str
    """
    return secho(message, fg='green', bold=True)
