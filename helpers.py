import functools
import inspect
import typing

from exceptions import ArgumentTypeError


def check_simple_types(f: typing.Callable) -> typing.Callable:
    """A decorator that will check the types of the arguments at runtime.

    This has a limitation that it can only deal with a concrete number of
    positional arguments, each of which is annotated with a concrete type.
    This means that no fancy `typing` annotations will be supported."""
    spec = inspect.getfullargspec(f)
    annotations = [[name, spec.annotations[name]] for name in spec.args]

    @functools.wraps(f)
    def ret(*args):
        for i, arg in enumerate(args):
            if not isinstance(arg, annotations[i][1]):
                fmt = "Expecting {name} to be of type {typ}, was {realtyp} instead."
                raise ArgumentTypeError(fmt.format(name=annotations[i][0], typ=annotations[i][1], realtyp=type(arg)))
        return f(*args)

    return ret


def wrap_exceptions_with(ex: type(Exception), message='', level=Exception):
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except level as e:
                raise ex(message) from e

        return wrapped

    return decorator
