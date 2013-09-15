# -*- coding: utf-8 -*-
"""
tornado_server.decorators
~~~~~~~~~~~~~~~~~~~~~~~~~

Defines some useful decorators for the tornado server.
"""
import logging


def bye_on_error(fn):
    """
    This decorator ensures that if the wrapped function throws any unhandled
    exception we will execute the tornado BYE logic. We will then rethrow the
    caught exception to ensure that the log accurately reflects the events.

    This decorator should only be used on Participant object methods, so that
    the first argument is a reference to the object itself.
    """
    def wrapper(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except Exception:
            logging.error(
                "Hit unhandled exception. Cleaning up then rethrowing."
            )

            # This is nasty.
            args[0]._bye()('')

            raise

    return wrapper


def bye_on_error_cb(participant):
    """
    This decorator ensures that if the wrapped function throws any unhandled
    exception we will execute the tornado BYE logic. We will then rethrow the
    caught exception to ensure that the log accurately reflects the events.

    This decorator should only be used on callbacks, or functions that can be
    passed a participant object.
    """
    def outer_wrapper(fn):
        def wrapper(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            except Exception:
                logging.error(
                    "Hit unhandled exception. Cleaning up then rethrowing."
                )

                # This is nasty.
                participant._bye()('')

                raise

        return wrapper

    return outer_wrapper
