"""
Safe logging utilities to prevent recursion errors in the logging system.

This module provides logging functions that are protected against recursion
and other logging-related errors that can cause infinite loops.
"""



def safe_log(level, message, logger_name=None):
    """
    Safely log a message with protection against recursion errors.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.ERROR)
        message: The message to log
        logger_name: Optional specific logger name to use
    """
    try:
        if logger_name:
            pass
        else:
            pass
    except RecursionError:
        # Silently ignore recursion errors to prevent infinite loops
        pass
    except Exception:
        # Silently ignore other logging errors
        pass


def safe_info(message, logger_name=None):
    """Safely log an info message."""
    safe_log(logging.INFO, message, logger_name)


def safe_warning(message, logger_name=None):
    """Safely log a warning message."""
    safe_log(logging.WARNING, message, logger_name)


def safe_error(message, logger_name=None):
    """Safely log an error message."""
    safe_log(logging.ERROR, message, logger_name)


def safe_debug(message, logger_name=None):
    """Safely log a debug message."""
    safe_log(logging.DEBUG, message, logger_name)


def safe_exception(message, logger_name=None):
    """Safely log an exception with traceback."""
    try:
        if logger_name:
            pass
        else:
            pass
    except RecursionError:
        # Silently ignore recursion errors to prevent infinite loops
        pass
    except Exception:
        # Silently ignore other logging errors
        pass