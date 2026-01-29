# Home

<p align="center">
    <a href="https://github.com/durandtibo/aresnet/actions/workflows/ci.yaml">
        <img alt="CI" src="https://github.com/durandtibo/aresnet/actions/workflows/ci.yaml/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/aresnet/actions/workflows/nightly-tests.yaml">
        <img alt="Nightly Tests" src="https://github.com/durandtibo/aresnet/actions/workflows/nightly-tests.yaml/badge.svg">
    </a>
    <a href="https://github.com/durandtibo/aresnet/actions/workflows/nightly-package.yaml">
        <img alt="Nightly Package Tests" src="https://github.com/durandtibo/aresnet/actions/workflows/nightly-package.yaml/badge.svg">
    </a>
    <a href="https://codecov.io/gh/durandtibo/aresnet">
        <img alt="Codecov" src="https://codecov.io/gh/durandtibo/aresnet/branch/main/graph/badge.svg">
    </a>
    <br/>
    <a href="https://durandtibo.github.io/aresnet/">
        <img alt="Documentation" src="https://github.com/durandtibo/aresnet/actions/workflows/docs.yaml/badge.svg">
    </a>
    <a href="https://durandtibo.github.io/aresnet/dev/">
        <img alt="Documentation" src="https://github.com/durandtibo/aresnet/actions/workflows/docs-dev.yaml/badge.svg">
    </a>
    <br/>
    <a href="https://github.com/psf/black">
        <img  alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg">
    </a>
    <a href="https://google.github.io/styleguide/pyguide.html#s3.8-comments-and-docstrings">
        <img  alt="Doc style: google" src="https://img.shields.io/badge/%20style-google-3666d6.svg">
    </a>
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" style="max-width:100%;">
    </a>
    <a href="https://github.com/guilatrova/tryceratops">
        <img  alt="Doc style: google" src="https://img.shields.io/badge/try%2Fexcept%20style-tryceratops%20%F0%9F%A6%96%E2%9C%A8-black">
    </a>
    <br/>
    <a href="https://pypi.org/project/aresnet/">
        <img alt="PYPI version" src="https://img.shields.io/pypi/v/aresnet">
    </a>
    <a href="https://pypi.org/project/aresnet/">
        <img alt="Python" src="https://img.shields.io/pypi/pyversions/aresnet.svg">
    </a>
    <a href="https://opensource.org/licenses/BSD-3-Clause">
        <img alt="BSD-3-Clause" src="https://img.shields.io/pypi/l/aresnet">
    </a>
    <br/>
    <a href="https://pepy.tech/project/aresnet">
        <img  alt="Downloads" src="https://static.pepy.tech/badge/aresnet">
    </a>
    <a href="https://pepy.tech/project/aresnet">
        <img  alt="Monthly downloads" src="https://static.pepy.tech/badge/aresnet/month">
    </a>
    <br/>
</p>

## Overview

A Python library for general purpose object factories.
In particular, it focuses on dynamic object factory implementations where objects can be registered
dynamically without changing the code of the factory.
An object factory can be used to instantiate an object from its configuration.
The current implementation contains both abstract factory and registry approaches.

**factory**

```python
from aresnet import factory


class MyClass:
    pass


obj = factory("MyClass")
print(obj)
```

**[abstract factory](user/abstract_factory.md)**

```python
from aresnet import AbstractFactory


class BaseClass(metaclass=AbstractFactory):
    pass


class MyClass(BaseClass):
    pass


obj = BaseClass.factory("MyClass")
print(obj)
```

*Output*:

```textmate
<__main__.MyClass object at 0x...>
```

**[registry](user/registry.md)**

```python
from aresnet import Registry

registry = Registry()


@registry.register()
class MyClass:
    pass


obj = registry.factory("MyClass")
print(obj)
```

```textmate
<__main__.MyClass object at 0x...>
```

## API stability

:warning: While `aresnet` is in development stage, no API is guaranteed to be stable from one
release to the next.
In fact, it is very likely that the API will change multiple times before a stable 1.0.0 release.
In practice, this means that upgrading `aresnet` to a new version will possibly break any code
that
was using the old version of `aresnet`.

## License

`aresnet` is licensed under BSD 3-Clause "New" or "Revised" license available
in [LICENSE](https://github.com/durandtibo/aresnet/blob/main/LICENSE) file.
