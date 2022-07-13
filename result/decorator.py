def outer_wrapper(event: str, level: int, bool_param: bool):
    def decorator(func: None):
        def inner_wrapper():








def decorator1(func: None):
    def inner_wrapper():






def decorator2(func: None):
    def inner_wrapper():






@decorator1    
@outer_wrapper("string_event", 2, bool_param=True)    
@decorator2
def fetch(a: None, b: None):
    ...
