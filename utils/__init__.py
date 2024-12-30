import json
import random
import string


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
