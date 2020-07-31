from time import sleep

from pytest import raises as assert_raises


def retry_on_exception(func, args=[], kwargs={}, exception=Exception, attempts=8):
    """
    Retry func(*args, **kwargs) with exponential backoff, starting from 100ms delay.

    Given:
    >>> def myfunc(arg, kwarg=True):
    ...     print(arg, kwarg)
    ...     1/0

    >>> with assert_raises(ZeroDivisionError):
    ...     retry_on_exception(myfunc, args=['hi'], kwargs={"kwarg": False}, exception=(ZeroDivisionError,), attempts=3)
    hi False
    sleeping 0.1
    hi False
    sleeping 0.2
    hi False
    """
    for attempt in range(attempts):
        try:
            return func(*args, **kwargs)
        except exception:
            if attempt < attempts-1:
                print("sleeping %s" % (.1*2**attempt))
                sleep(.1*2**attempt)
            else:
                raise
