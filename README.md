# Lobster v0.1 alpha
### Idiomatic Python to (**Python**, C, Rust, Go) transpiler
#### Inspired by [Pyrs](https://github.com/konchunas/pyrs) project

Lobster's original idea is about to write low-level, high-performance extensions of the Python language in Python itself, without knowledge of C/Cython, [CAPI](https://docs.python.org/3/c-api/index.html), [CFFI](https://cffi.readthedocs.io/en/latest/#) and else.
In simple terms, you write slow Python code, and Lobster will traspile your Python source code into C, Rust, Go source code. Some implementations allow for instant integration of extensions into your Python Environment. For example, Rust has [Pyo3](https://pyo3.rs/v0.16.4/) and [Maturin](https://github.com/PyO3/maturin), and C has [CFFI](https://cffi.readthedocs.io/en/latest/#), [CAPI](https://docs.python.org/3/c-api/index.html), [Cython](https://cython.org/)
