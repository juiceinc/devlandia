"""Provides standardized methods and colors for various console message
outputs.
"""
from click import secho
from dateutil.relativedelta import relativedelta
from datetime import datetime


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
    """ Generate a human readable time difference, use the 2 largest time intervals
    if the the first part is a one for example: "1 hour, 30 minutes ago", but
    just use the largest time interval in other cases, for example: "18 hours ago"

    :param dt: datetime we want to find the difference between current time
    :type dt: datetime
    """

    attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
    human_readable = lambda delta: ['%d %s' % (getattr(delta, attr), getattr(delta, attr) > 1 and attr or attr[:-1]) 
        for attr in attrs if getattr(delta, attr)]

    parts = relativedelta(datetime.now(), dt)
    readable_parts = human_readable(parts)

    # Show more detail when the first part is "1 day" or "1 hour"
    if readable_parts and readable_parts[0].startswith('1 '):
        readable_timediff = ', '.join(readable_parts[:2]) + ' ago'
    else:
        readable_timediff = ', '.join(readable_parts[:1]) + ' ago'

    return readable_timediff
