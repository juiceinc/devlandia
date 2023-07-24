"""Provides standardized methods and colors for various console message
outputs.
"""
from click import secho
from datetime import datetime, timedelta
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

def compare_human_readable(old_time, new_time):
    """ Compare the difference in age between 2 human readable times

    :param new_time: human readable diff sliced into list to be [ number, date operand ]
    :param old_time: same as param new but older
    """
    now = datetime.now()
    if new_time[1] == 'months':
        new_time[1] = 'weeks'
        new_time[0] = int(new_time[0]) / 4
    if old_time[1] == 'months':
        old_time[1] = 'weeks'
        old_time[0] = int(old_time[0]) / 4
    old_date = now - timedelta(**{old_time[1]:int(old_time[0])})
    new_date = now - timedelta(**{new_time[1]: int(new_time[0])})
    return abs(old_date - new_date)
