import argparse
import contextlib
import pathlib
import sys
from datetime import datetime
from typing import Mapping, TextIO, Tuple, Iterable, Optional

import semver
import toml

from poetry2conda import __version__


def convert(
    file: TextIO, include_dev: bool = False, extras: Optional[Iterable[str]] = None
) -> str:
    """ Convert a pyproject.toml file to a conda environment YAML

    This is the main function of poetry2conda, where all parsing, converting,
    etc. gets done.

    Parameters
    ----------
    file
        A file-like object containing a pyproject.toml file.
    include_dev
        Whether to include the dev dependencies in the resulting environment.
    extras
        The name of extras to include in the output.  Can be None or empty
        for no extras.

    Returns
    -------
    The contents of an environment.yaml file as a string.

    """
    if extras is None:
        extras = []
    poetry2conda_config, poetry_config = parse_pyproject_toml(file)
    env_name = poetry2conda_config["name"]
    poetry_dependencies = poetry_config.get("dependencies", {})
    if include_dev:
        poetry_dependencies.update(poetry_config.get("dev-dependencies", {}))
    poetry_extras = poetry_config.get("extras", {})
    # We mark the items listed in the selected extras as non-optional
    for extra in extras:
        for item in poetry_extras[extra]:
            dep = poetry_dependencies[item]
            if isinstance(dep, dict):
                dep["optional"] = False
    conda_constraints = poetry2conda_config.get("dependencies", {})

    dependencies, pip_dependencies = collect_dependencies(
        poetry_dependencies, conda_constraints
    )
    conda_yaml = to_yaml_string(env_name, dependencies, pip_dependencies)
    return conda_yaml


def convert_version(spec_str: str) -> str:
    """ Convert a poetry version spec to a conda-compatible version spec.

    Poetry accepts tilde and caret version specs, but conda does not support
    them. This function uses the `poetry-semver` package to parse it and
    transform it to regular version spec ranges.

    Parameters
    ----------
    spec_str
        A poetry version specification string.

    Returns
    -------
    The same version specification without tilde or caret.

    """
    spec = semver.parse_constraint(spec_str)
    if isinstance(spec, semver.Version):
        converted = f"=={str(spec)}"
    elif isinstance(spec, semver.VersionRange):
        converted = str(spec)
    elif isinstance(spec, semver.VersionUnion):
        raise ValueError("Complex version constraints are not supported at the moment.")
    return converted


def parse_pyproject_toml(file: TextIO) -> Tuple[Mapping, Mapping]:
    """ Parse a pyproject.toml file

     This function assumes that the pyproject.toml contains a poetry and
     poetry2conda config sections.

    Parameters
    ----------
    file
        A file-like object containing a pyproject.toml file.

    Returns
    -------
    A tuple with the poetry2conda and poetry config.

    Raises
    ------
    RuntimeError
        When an expected configuration section is missing.


    """
    pyproject_toml = toml.loads(file.read())
    poetry_config = pyproject_toml.get("tool", {}).get("poetry", {})
    if not poetry_config:
        raise RuntimeError(f"tool.poetry section was not found on {file.name}")

    poetry2conda_config = pyproject_toml.get("tool", {}).get("poetry2conda", {})
    if not poetry2conda_config:
        raise RuntimeError(f"tool.poetry2conda section was not found on {file.name}")

    if "name" not in poetry2conda_config or not isinstance(
        poetry2conda_config["name"], str
    ):
        raise RuntimeError(f"tool.poetry2conda.name entry was not found on {file.name}")

    return poetry2conda_config, poetry_config


def collect_dependencies(
    poetry_dependencies: Mapping, conda_constraints: Mapping
) -> Tuple[Mapping, Mapping]:
    """ Organize and apply conda constraints to dependencies

    Parameters
    ----------
    poetry_dependencies
        A dictionary with dependencies as declared with poetry.
    conda_constraints
        A dictionary with conda constraints as declared with poetry2conda.

    Returns
    -------
    A tuple with the modified dependencies and the dependencies that must be
    installed with pip.

    """
    dependencies = {}
    pip_dependencies = {}

    # 1. Do a first pass to change pip to conda packages
    for name, conda_dict in conda_constraints.items():
        if name in poetry_dependencies and "git" in poetry_dependencies[name]:
            poetry_dependencies[name] = conda_dict["version"]

    # 2. Now do the conversion
    for name, constraint in poetry_dependencies.items():
        if isinstance(constraint, str):
            dependencies[name] = convert_version(constraint)
        elif isinstance(constraint, dict):
            if constraint.get("optional", False):
                continue
            if "git" in constraint:
                git = constraint["git"]
                tag = constraint["tag"]
                pip_dependencies[f"git+{git}@{tag}#egg={name}"] = None
            elif "version" in constraint:
                dependencies[name] = convert_version(constraint["version"])
            else:
                raise ValueError(
                    f"This converter only supports normal dependencies and "
                    f"git dependencies. No path, url, python restricted, "
                    f"environment markers or multiple constraints. In your "
                    f'case, check the "{name}" dependency. Sorry.'
                )
        else:
            raise ValueError(
                f"This converter only supports normal dependencies and "
                f"git dependencies. No multiple constraints. In your "
                f'case, check the "{name}" dependency. Sorry.'
            )

        if name in conda_constraints:
            conda_dict = conda_constraints[name]
            if "name" in conda_dict:
                new_name = conda_dict["name"]
                dependencies[new_name] = dependencies.pop(name)
                name = new_name
            # do channel last, because it may move from dependencies to pip_dependencies
            if "channel" in conda_dict:
                channel = conda_dict["channel"]
                if channel == "pip":
                    pip_dependencies[name] = dependencies.pop(name)
                else:
                    new_name = f"{channel}::{name}"
                    dependencies[new_name] = dependencies.pop(name)

    if pip_dependencies:
        dependencies["pip"] = None

    return dependencies, pip_dependencies


def to_yaml_string(
    env_name: str, dependencies: Mapping, pip_dependencies: Mapping
) -> str:
    """ Converts dependencies to a string in YAML format.

    Note that there is no third party library to manage the YAML format. This is
    to avoid an additional package dependency (like pyyaml, which is already
    one of the packages that behaves badly in conda+pip mixed environments).
    But also because our YAML is very simple

    Parameters
    ----------
    env_name
        Name for the conda environment.
    dependencies
        Regular conda dependencies.
    pip_dependencies
        Pure pip dependencies.

    Returns
    -------
    A string with an environment.yaml definition usable by conda.

    """
    deps_str = []
    for name, version in dependencies.items():
        version = version or ""
        deps_str.append(f"  - {name}{version}")
    if pip_dependencies:
        deps_str.append(f"  - pip:")
    for name, version in pip_dependencies.items():
        version = version or ""
        deps_str.append(f"    - {name}{version}")
    deps_str = "\n".join(deps_str)

    date_str = datetime.now().strftime("%c")
    conda_yaml = f"""
###############################################################################
# NOTE: This file has been auto-generated by poetry2conda
#       poetry2conda version = {__version__}
#       date: {date_str}
###############################################################################
# If you want to change the contents of this file, you should probably change
# the pyproject.toml file and then use poetry2conda again to update this file.
# Alternatively, stop using (ana)conda.
###############################################################################
name: {env_name}
dependencies:
{deps_str}
""".lstrip()
    return conda_yaml


def write_file(filename: str, contents: str) -> None:
    context = contextlib.ExitStack()
    if filename == '-':
        f = sys.stdout
    else:
        environment_yaml = pathlib.Path(filename)
        if not environment_yaml.exists():
            environment_yaml.parent.mkdir(parents=True, exist_ok=True)
        f = context.enter_context(environment_yaml.open('w'))

    with context:
        f.write(contents)


def main():
    parser = argparse.ArgumentParser(
        description="Convert a poetry-based pyproject.toml "
        "to a conda environment.yaml"
    )
    parser.add_argument(
        "pyproject",
        metavar="TOML",
        type=argparse.FileType("r"),
        help="pyproject.toml input file.",
    )
    parser.add_argument(
        "environment",
        metavar="YAML",
        type=str,
        help="environment.yaml output file.",
    )
    parser.add_argument(
        "--dev", action="store_true", help="include dev dependencies",
    )
    parser.add_argument(
        "--extras", "-E", action="append", help="Add extra requirements",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s (version {__version__})"
    )
    args = parser.parse_args()
    converted_obj = convert(args.pyproject, include_dev=args.dev, extras=args.extras)
    write_file(args.environment, converted_obj)


if __name__ == "__main__":
    main()
