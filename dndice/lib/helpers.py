"""A few helper decorators to simplify construction of the code."""
import functools
import inspect
import typing

from .exceptions import ArgumentTypeError


def check_simple_types(f: typing.Callable) -> typing.Callable:
    """A decorator that will check the types of the arguments at runtime.

    This has a limitation that it can only deal with a concrete number
    of positional arguments, each of which is annotated with a concrete
    type. This means that no fancy `typing` annotations will be
    supported.
    """
    spec = inspect.getfullargspec(f)
    annotations = [[name, spec.annotations[name]] for name in spec.args]

    @functools.wraps(f)
    def ret(*args):
        for i, arg in enumerate(args):
            if not isinstance(arg, annotations[i][1]):
                fmt = "Expecting {name} to be of type {typ}, was {realtyp} instead."
                raise ArgumentTypeError(fmt.format(name=annotations[i][0],
                                                   typ=annotations[i][1],
                                                   realtyp=type(arg)))
        return f(*args)

    return ret


def wrap_exceptions_with(ex: type(Exception), message='', target=Exception):
    """Catch exceptions and rethrow them wrapped in an exception of our choosing.

    This is mainly for the purpose of catching whatever builtin
    exceptions might be thrown and showing them to the outside world as
    custom module exceptions. That way an external importer can just
    catch the RollError and thus catch every exception thrown by this
    module.

    ``target`` specifies what to catch and therefore wrap. By default
    it's ``Exception`` to cast a wide net but note that you can catch
    any specific exception you please, or a set of exceptions if you
    pass in a tuple of exception classes.

    And yes, this is just try/catch/rethrow. It's more decorative this
    way though. Plus saves you some indentation as you're trying to wrap
    an entire function.

    :param ex: The exception to use as wrapper.
    :param message: A custom message to use for the wrapper exception.
    :param target: Which exception(s) you want to catch.
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except target as e:
                raise ex(message) from e

        return wrapped

    return decorator
