# Pipeline Documentation

This document describes how to execute the analysis pipeline using the command-line interface.

## 1. Starting the Pipeline

The pipeline is orchestrated using [Prefect](https://www.prefect.io/). The necessary Prefect infrastructure (work pool and worker) is automatically bootstrapped when you run the pipeline command.

### How it works
The entry point `faf28_workflows/bootstrap.py` checks if the Prefect API is reachable. It then ensures a local work pool named `concurrency-limited-pool` exists and starts a worker named `busybee` to process jobs.

## 2. Running the CLI

The project installs a command-line tool named `pipeline`.

### Basic Usage

Check available commands:
```bash
pipeline --help
```

List available jobs/steps in the pipeline:
```bash
pipeline list-jobs
```

Run the pipeline for a specific input:
```bash
pipeline run <INPUT_DATA>
```

Run the pipeline for ALL data:
```bash
pipeline run all
```

### Options

*   `--start-from <JOB_NAME>`: Start execution from a specific job step.
*   `--stop-after <JOB_NAME>`: Stop execution after a specific job step.
*   `--skip-existing / -x`: Skip steps that have already been completed.
*   `--log-level`: Set logging level (INFO, DEBUG, WARNING, ERROR).

Example:
```bash
pipeline run "path/to/image.tiff" --skip-existing --log-level DEBUG
```

## 3. Pipeline Definition

The executable `pipeline` is defined in `pyproject.toml` under `[project.scripts]`.

```toml
[project.scripts]
pipeline = "faf28_workflows.bootstrap:main"
```

This acts as the main entry point which handles the Prefect bootstrap process before handing off control to the actual CLI logic in `faf28_workflows/cli.py`.
