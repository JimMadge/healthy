# healthy

![CI](https://github.com/JimMadge/healthy/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/JimMadge/healthy/branch/main/graph/badge.svg?token=4T6H1FW6IO)](https://codecov.io/gh/JimMadge/healthy)

Restart docker containers which fail their HEALTHCHECK.

## Installation

Clone this repository

```
$ git clone https://github.com/JimMadge/healthy.git
$ cd healthy
```

Then build and install with pip

```
$ pip install .
```

## Usage

Run `healthy` to check the health status of any running containers. The program
will print a list of running containers, their status and any action taken. For
example,

```
$ healthy
nginx - healthy - skipping
redis - no health check- skipping
postgres - unhealthy - restarting
```

## Development/testing

This project uses poetry for development. To install the projects dependencies
run

```
$ poetry install
```

To run the tests, make sure the docker daemon is running and run

```
poetry run pytest
```
