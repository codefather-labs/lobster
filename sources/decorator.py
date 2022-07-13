def outer_wrapper(event: str, level: int, bool_param: bool):
    def decorator(func):
        def inner_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return result

        return inner_wrapper

    return decorator


def decorator1(func):
    def inner_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result

    return inner_wrapper


def decorator2(func):
    def inner_wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result

    return inner_wrapper


@decorator1
@outer_wrapper("string_event", 2, bool_param=True)
@decorator2
def fetch(a, b): ...
