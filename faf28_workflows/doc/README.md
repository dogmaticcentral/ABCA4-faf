# The `config_factory` solution in `PipelineConfig`

Big picture first, because otherwise the `config_factory` looks like a cursed lambda nesting doll.
## An explanation of `dataclasses.field`

See [dataclasses_field.md](dataclasses_field.md)

## An explanation of the type of `config_factory`
See [config_factory.md](config_factory.md)

----
## The definition of `PipelineConfig`

This code defines:

* a **JobSpec**: a *recipe* for creating one analysis job
* a **PipelineDefinition**: an *ordered list* of those recipes

Nothing actually runs here. Nothing executes. This is a **declarative pipeline description**, not the pipeline itself. You’re describing *how to create jobs later*, not creating them now.

---

## What `JobSpec` actually represents

```python
@dataclass
class JobSpec:
    name: str
    job_class: type[FafAnalysis]
    config_factory: Callable[[], dict[str, Any]]
    description: str = ""
```

A `JobSpec` answers exactly one question:

> “When the time comes, how do I instantiate this job?”

It stores:

1. **name**
   A unique identifier. Bookkeeping, nothing philosophical.

2. **job_class**
   A subclass of `FafAnalysis`. This is the *constructor* you will eventually call.

3. **config_factory**
   This is the interesting bit.
   It is a **zero-argument callable** that returns a dict of keyword arguments to pass into `job_class`.

4. **description**
   Human-readable fluff.

So conceptually:

```
JobSpec = (class to instantiate) + (function that produces constructor kwargs)
```

---

## The `config_factory` thing, without mysticism

This line tends to confuse people:

```python
config_factory: Callable[[], dict[str, Any]] = field(
    default_factory=lambda: lambda: {}
)
```

Yes, it’s ugly. No, it’s not deep.

### Why the double lambda?

* `default_factory=` is a **dataclasses requirement**
* It must be a callable that produces the default value
* The default value itself must be a callable (`config_factory`)

So:

* outer lambda: creates the default value
* inner lambda: is the default value

Expanded:

```python
def default_config_factory():
    return {}

def default_field_factory():
    return default_config_factory

config_factory = field(default_factory=default_field_factory)
```


---

## What `create_instance` does

```python
def create_instance(self) -> FafAnalysis:
    config = self.config_factory()
    return self.job_class(**config)
```

This is the entire reason `config_factory` exists.

Execution flow:

1. Call `config_factory()`
   You get a dict like `{"threshold": 0.8, "use_cache": True}`
2. Instantiate the job
   `MyAnalysis(threshold=0.8, use_cache=True)`

Why not just store a dict directly?

Because:

* configs may depend on runtime state
* configs may differ per execution
* configs may need to be *recomputed*, not reused
* mutable defaults are a footgun and Python already has enough of those

So instead of storing **data**, you store a **function that produces data**.

---

## `PipelineDefinition`: a job registry with ordering

This class is boring in a good way.

```python
self._jobs: list[JobSpec] = []
self._job_index: dict[str, int] = {}
```

* `_jobs` preserves order
* `_job_index` gives O(1) lookup by name

### `add_job`

```python
def add_job(...):
    if name in self._job_index:
        raise ValueError(...)
```

So job names must be unique. Sensible.

```python
spec = JobSpec(
    name=name,
    job_class=job_class,
    config_factory=config_factory or (lambda: {}),
    description=description,
)
```

Key detail:

* If you don’t provide a `config_factory`, it silently uses `lambda: {}`
* This *overrides* the dataclass default
* Meaning: every job always has a callable, no conditionals later

That’s deliberate. It keeps `create_instance()` dead simple.

---

## How this is meant to be used (example)

Let’s assume a concrete `FafAnalysis` subclass:

```python
class SegmentRetina(FafAnalysis):
    def __init__(self, model_path: str, threshold: float):
        ...
```

### Define a pipeline

```python
pipeline = PipelineDefinition(name="faf_pipeline")

pipeline.add_job(
    name="segmentation",
    job_class=SegmentRetina,
    config_factory=lambda: {
        "model_path": "/models/retina_v3.pt",
        "threshold": 0.85,
    },
    description="Segment retinal layers",
)
```

Nothing is instantiated yet. No models loaded. No GPU crying.

---

### Later, when you want actual job objects

```python
for spec in pipeline._jobs:
    job = spec.create_instance()
    job.run()
```

Each iteration:

* calls the factory
* gets fresh config
* instantiates a fresh analysis object

If you want **dynamic config**, that’s where this shines:

```python
def make_config():
    return {
        "model_path": os.environ["MODEL_PATH"],
        "threshold": get_threshold_from_db(),
    }

pipeline.add_job(
    name="segmentation",
    job_class=SegmentRetina,
    config_factory=make_config,
)
```

Now the config reflects **runtime state**, not whatever was true when the pipeline was defined.

---

## Why this design exists at all

This pattern solves three real problems:

1. **No premature instantiation**
   Pipelines can be defined at import time without side effects.

2. **Runtime-dependent configuration**
   Especially useful for Prefect, where flows may run hours later.

3. **Clean separation of structure vs execution**
   Pipeline definition is static. Job creation is dynamic.

If you’ve ever fought Prefect trying to serialize half your object graph, this is why someone wrote it this way.

---

## Blunt assessment

* The `config_factory` naming is good
* The double lambda default is ugly but unavoidable
* The design is solid and scales well
* This is textbook “factory pattern”, just without the academic chest-beating

It’s not clever. It’s careful. Which is rarer and more useful.


# Elaboration - why config cannot be a dictionary

Good. This is the right place to be confused, because *if nothing is dynamic*, the factory looks like ceremonial nonsense.

So let’s strip away dataclasses, Prefect, and type hints and talk like adults.

You’re proposing this alternative universe:

```python
class JobSpec:
    def __init__(self, job_class, config: dict):
        self.job_class = job_class
        self.config = config
```

and later:

```python
job = self.job_class(**self.config)
```

Totally reasonable. Works fine. No one dies.

Now here’s the key point, stated plainly:

> **If the config is truly static, there is no advantage. None. Zero.**

Using a function instead of a dict only matters when *time* matters.

Everything below is about **when** the config is evaluated.

---

## The only difference that matters: time

### Dictionary approach (your proposal)

```python
pipeline.add_job(
    job_class=SegmentRetina,
    config={
        "threshold": get_threshold_from_db(),
        "model_path": os.environ["MODEL_PATH"],
    }
)
```

What happens?

* `get_threshold_from_db()` runs **immediately**
* `os.environ["MODEL_PATH"]` is read **immediately**
* The values are frozen into the pipeline definition

The pipeline now contains **results**, not **logic**.

---

### Factory approach

```python
pipeline.add_job(
    job_class=SegmentRetina,
    config_factory=lambda: {
        "threshold": get_threshold_from_db(),
        "model_path": os.environ["MODEL_PATH"],
    }
)
```

What happens?

* Nothing runs yet
* You store *instructions*, not *values*
* The database and environment are touched **later**, when the job is instantiated

That’s it. That’s the entire difference.

---

## Why this matters in real systems

Here are situations where the dictionary approach actively breaks things.

### 1. Pipelines defined at import time

Most pipelines are defined like this:

```python
# pipeline.py
pipeline = PipelineDefinition()

pipeline.add_job(...)
```

Import time is:

* before Prefect runs
* before workers exist
* before secrets are injected
* sometimes on a completely different machine

If your config is a dict, all side effects happen **during import**.

That’s how you get:

* missing env vars
* stale DB values
* credentials pulled on the wrong host

The factory delays evaluation until execution time.

---

### 2. Multiple runs, different configs

Say the same pipeline runs every night.

With a dict:

```python
config = {"date": date.today()}
```

Congratulations, your “daily” job always uses the date from the day the pipeline was defined.

With a factory:

```python
lambda: {"date": date.today()}
```

Each run gets the correct date.

---

### 3. Mutability landmines

If you store a dict:

```python
config = {"options": []}
```

And one job mutates it:

```python
self.options.append("foo")
```

Now every future job sees the mutated config.

With a factory:

```python
lambda: {"options": []}
```

Each job gets a fresh dict. No shared state. No weird ghosts.

---

### 4. Conditional config

You can do this:

```python
def make_config():
    if running_on_gpu():
        return {"device": "cuda"}
    return {"device": "cpu"}
```

You *cannot* express this cleanly with a static dict without inventing your own mini-language.

---

## When a dict is genuinely fine

If **all** of the following are true:

* config values are literals
* they never depend on time, env, DB, filesystem, or runtime context
* they are never mutated
* the pipeline is defined right before execution

Then yes. A dict is simpler and clearer.

Using a factory there is architectural overkill. People do it anyway because frameworks train them to fear the future.

---

## The honest summary

* A dict stores **answers**
* A factory stores **questions**

If the answer never changes, asking the question repeatedly is pointless.

This design exists because in workflow systems, configs almost always *do* change, often in ways that are painful to debug after the fact.

If you’re writing a small script, use the dict and sleep well.
If you’re writing a pipeline that survives imports, scheduling, retries, workers, and time, the factory saves you from extremely stupid bugs later.

No mysticism. Just timing.
