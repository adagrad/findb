import logging

_log = logging.getLogger(__name__)


def call_silent(func, default=None, log=False, log_ctx=None):
    try:
        return func()
    except Exception as e:
        if log:
            _log.warning(f"failed {func} call: {log_ctx}: {e}")
        return default(e) if callable(default) else default
