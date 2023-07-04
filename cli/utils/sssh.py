import warnings

_default_warn = warnings.warn


def warn(warn, kind, *args, **kwargs):
    if kind not in (DeprecationWarning, FutureWarning):
        return _default_warn(warn, kind, *args, **kwargs)
    return None


warnings.warn = warn
warnings.filterwarnings("ignore", category=FutureWarning)

import logging  # noqa: E402

logging.getLogger("numexpr").setLevel(logging.WARNING)
