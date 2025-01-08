import json
import random
import string
import time


def generate_random_string(length: int = 4):
    """
    Generate a random alphanumeric string of specified length.
    """
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def rp_attach(logger, msg, filename, data, filetype):
    """
    Attach data to a report portal log entry.
    """
    logger(msg, attachment={"name": filename, "data": data, "mime": filetype})


def rp_attach_json(logger, msg, filename, data):
    """
    Attach JSON data to a report portal log entry.
    """
    if isinstance(data, dict):
        data = json.dumps(data)
    rp_attach(logger, msg, filename, data, "application/json")


def rp_attach_plain(logger, msg, filename, data):
    """
    Attach plain text data to a report portal log entry.
    """
    rp_attach(logger, msg, filename, data, "text/plain")


def wait_for(func, timeout=60, first=0.0, step=1.0, args=None, kwargs=None):
    """
    Wait until func() evaluates to True.

    :param timeout: Timeout in seconds
    :param first: Time to sleep before first attempt
    :param step: Time to sleep between attempts in seconds
    :param args: Positional arguments to func
    :param kwargs: Keyword arguments to func
    """
    args = args or []
    kwargs = kwargs or {}

    start_time = time.monotonic()
    end_time = start_time + timeout

    time.sleep(first)

    while time.monotonic() < end_time:
        output = func(*args, **kwargs)
        if output:
            return output
        time.sleep(step)

    return None
