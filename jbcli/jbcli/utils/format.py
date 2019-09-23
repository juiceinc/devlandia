"""Provides standardized methods and colors for various console message
outputs.
"""
from click import secho
from dateutil.relativedelta import relativedelta
from datetime import datetime
from humanize import naturaltime


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


def human_readable_timediff(dt):
    """ Generate a human readable time difference between this time and now

    :param dt: datetime we want to find the difference between current time
    :type dt: datetime
    """
    return naturaltime(datetime.now() - dt)
