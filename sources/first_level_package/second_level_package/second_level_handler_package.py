from sources.first_level_package.second_level_package. \
    third_level_package. \
    third_level_handler_package import third_level_func1, third_level_func2


def second_level_handler(arg: str):
    return third_level_func1(arg) + third_level_func2(arg)
