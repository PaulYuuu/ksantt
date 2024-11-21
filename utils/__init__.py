import json
import random
import string


def generate_random_string(length: int = 4) -> str:
    """Generate a random alphanumeric string."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def rp_attach(logger, msg, filename, data, filetype):
    logger(msg, attachment={"name": filename, "data": data, "mime": filetype})


def rp_attach_json(logger, msg, filename, data):
    if isinstance(data, dict):
        data = json.dumps(data)
    rp_attach(logger, msg, filename, data, "application/json")


def rp_attach_plain(logger, msg, filename, data):
    rp_attach(logger, msg, filename, data, "text/plain")
