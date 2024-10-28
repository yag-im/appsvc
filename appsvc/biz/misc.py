import logging
import typing as t

log = logging.getLogger("appsvc")


@t.no_type_check
def log_input_output(func):
    def wrap(*args, **kwargs):
        # Log the function name and arguments
        log.debug("calling %s with args: %s, kwargs: %s", func.__name__, args, kwargs)

        # Call the original function
        result = func(*args, **kwargs)

        # Log the return value
        log.debug("%s returned: %s", func.__name__, repr(result))

        # Return the result
        return result

    return wrap
