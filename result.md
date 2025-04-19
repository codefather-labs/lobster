```python
# third_level_handler_package.py
def third_level_func1(arg: str):
    return (arg + '1')

def third_level_func2(arg: str):
    return (arg + '2')
```

```python
# second_level_handler_package.py
def third_level_func1(arg: str):
    return (arg + '1')

def third_level_func2(arg: str):
    return (arg + '2')

from sources.first_level_package.second_level_package.third_level_package.third_level_handler_package import third_level_func1, third_level_func2

def second_level_handler(arg: str):
    return (third_level_func1(arg) + third_level_func2(arg))
```

```python
# first_level_handler_package.py
def third_level_func1(arg: str):
    return (arg + '1')

def third_level_func2(arg: str):
    return (arg + '2')

from sources.first_level_package.second_level_package.third_level_package.third_level_handler_package import third_level_func1, third_level_func2

def second_level_handler(arg: str):
    return (third_level_func1(arg) + third_level_func2(arg))

from sources.first_level_package.second_level_package.second_level_handler_package import second_level_handler

def first_level_handler(arg: str):
    return second_level_handler(arg)
```

```python
# multiply_import.py
def third_level_func1(arg: str):
    return (arg + '1')

def third_level_func2(arg: str):
    return (arg + '2')

from sources.first_level_package.second_level_package.third_level_package.third_level_handler_package import third_level_func1, third_level_func2

def second_level_handler(arg: str):
    return (third_level_func1(arg) + third_level_func2(arg))

from sources.first_level_package.second_level_package.second_level_handler_package import second_level_handler

def first_level_handler(arg: str):
    return second_level_handler(arg)

from sources.first_level_package.first_level_handler_package import first_level_handler

first_level_handler()
```