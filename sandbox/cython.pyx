# def func1(arg0: str,
#           arg1: str = None,
#           arg2: dict = {},
#           arg3: list = [],
#           arg4: str = "DEFAULT4"):
#     def inner(): pass
#
#     def inner2(): ...

cdef func1(str arg0, str arg1 = None, dict arg2 = {}, list arg3 = [], str arg4 = "DEFAULT4"):
    cdef inner(): pass
    cdef inner2(): ...
