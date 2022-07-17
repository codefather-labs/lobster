from sources.first_level_package. \
    second_level_package. \
    second_level_handler_package \
    import second_level_handler


def first_level_handler(arg: str): return second_level_handler(arg)
