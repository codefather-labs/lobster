from abc import ABC, abstractmethod
from typing import Sequence, AsyncGenerator, Generator, Callable


def is_option(arg1: dict, arg2: str, arg3: Sequence[int]) -> bool:
    return True


class A(ABC):
    class Meta:
        abstract = True

    @abstractmethod
    def __instance(self) -> Callable: raise NotImplementedError()

    @abstractmethod
    def fetch(self) -> Generator: raise NotImplementedError()


class B(ABC):
    class Meta:
        abstract = True

    @abstractmethod
    async def async_fetch(self) -> AsyncGenerator: raise NotImplementedError()


class Model(A, B):
    class Meta:
        abstract = False

    def __instance(self) -> Callable: ...

    def fetch(self) -> Generator: ...

    async def async_fetch(self) -> AsyncGenerator: ...

    @property
    def instance(self):
        return self.__instance()
