# Arches-Doorstep Link Application

(credit to @chiatt for the template)

Arches-Doorstep is a wrapper application for adding doorstep-driven validation to
Arches projects. [Doorstep](https://github.com/flaxandteal/doorstep) is an open
source project for chaining validation logic with a standard schema, to make
complex validations quick to write and integrate into a single consolidated
QA report.

You can add doorstep to an Arches project in just a few easy steps.

1. Install if from this repo (or clone this repo and pip install it locally). 
```
pip install git+https://github.com/flaxandteal/arches_doorstep.git
```

2. Add `"arches_doorstep"` to the INSTALLED_APPS setting in the demo project's settings.py file below the demo project:
```
INSTALLED_APPS = [
    ...
    "arches_doorstep",
]
```

3. Version your dependency on `"arches_doorstep"` in `pyproject.toml`:
```
dependencies = [
    "arches>=7.6.0,<7.7.0",
    "arches_doorstep==0.0.1",
]
```
