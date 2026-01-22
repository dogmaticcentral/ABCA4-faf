# `config_factory` field in JobSpec

Let's break it down clearly:

### What does `Callable[[], dict[str, Any]]` mean?

```python
Callable[  ← this is a special type from typing
    [ ],   ← parameter types go here (empty = no arguments)
    dict[str, Any]   ← return type
]
```

This means:

- It is a **callable** (something you can call with `()`)
- It **takes no arguments**  (`[]` is empty)
- It **returns** a dictionary `dict[str, Any]`

In plain English:

> `config_factory` is expected to be **a function (or other callable) that takes no arguments and returns a dictionary**.

### Most common forms you will see in practice

```python
# 1. Regular function
def make_config() -> dict[str, Any]:
    return {"threshold": 0.75, "normalize": True}

# 2. Lambda (very common in dataclasses)
config_factory = lambda: {"n_estimators": 100, "max_depth": 5}

# 3. functools.partial
from functools import partial
config_factory = partial(create_config, mode="light", version=2)

# 4. Method or classmethod (if bound later)
config_factory = SomeBuilder.build_light_config

# 5. closure / factory function
def _make_config_closure():
    cache = expensive_computation()
    def inner():
        return {"important_value": cache.value, "debug": False}
    return inner

config_factory = _make_config_closure()
```

### Why they used `default_factory=lambda: lambda: {}`

This is a very common (and safe) pattern when you want:

- each `JobSpec` instance to get **its own independent dict**
- avoid sharing the same mutable default object across instances

```python
# BAD – all instances share the same dict!
config_factory: Callable[[], dict] = lambda: {}   # ← mutable default

# GOOD – each call creates a new dict
config_factory: Callable[[], dict] = field(default_factory=lambda: lambda: {})
```

So the real default value is:

```python
lambda: {}    # a function that, when called, returns a fresh empty dict
```

### Summary – most concise answer

```text
callable_config (config_factory) is:

a function (or lambda / partial / bound method / closure)
that takes zero arguments
and returns a dict[str, Any]
```

Most idiomatic usage:

```python
config_factory = lambda: {"param1": 42, "flag": True}
# or
config_factory = lambda: dict(param1=42, flag=True)
```