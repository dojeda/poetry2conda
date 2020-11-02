import io

import yaml

from poetry2conda.convert import main


# foo, bar, baz, qux, quux, quuz, corge, grault, garply, waldo, fred, plugh, xyzzy, and thud;
SAMPLE_TOML = """\
[tool.poetry]
name = "bibimbap"
version = "1.2.3"
description = "Delicious korean food"
authors = ["David Ojeda <david.ojeda@gmail.com>"]
license = "MIT"

[[tool.poetry.source]]
name = "stable"
url = "https://private.repo.my/my/stable/+simple/"
default = true

[[tool.poetry.source]]
name = "edge"
url = "https://private.repo.my/my/edge/+simple/"

[tool.poetry.dependencies]
python = "^3.7"
foo = "^0.2.3"              # Example of a caret requirement whose major version is zero
bar = "^1.2.3"              # Example of a caret requirement whose major version is not zero
baz = "~0.4.5"              # Example of a tilde requirement whose major version is zero
qux = "~1.4.5"              # Example of a tilde requirement whose major version is not zero
quux = "2.34.5"             # Example of an exact version
quuz = ">=3.2"              # Example of an inequality
xyzzy = ">=2.1,<4.2"        # Example of two inequalities
spinach = "^19.10b0"        # Previously non-working version spec
grault = { git = "https://github.com/organization/repo.git", tag = "v2.7.4"}   # Example of a git package
pizza = {extras = ["pepperoni"], version = "^1.2.3"}  # Example of a package with extra requirements
chameleon = { git = "https://github.com/org/repo.git", tag = "v2.3" }
pudding = { version = "^1.0", optional = true }

[tool.poetry.extras]
dessert = ["pudding"]

[tool.poetry.dev-dependencies]
fork = "^1.2"

[tool.poetry2conda]
name = "bibimbap-env"

[tool.poetry2conda.dependencies]
bar = { channel = "conda-forge" }            # Example of a package on conda-forge
baz = { channel = "pip" }                    # Example of a pure pip package
qux = { name = "thud" }                      # Example of a package that changes names in conda
chameleon = { name = "lizard", channel = "animals", version = "^2.5.4" }  # Example of a package that changes from git to regular conda

[build-system]
requires = ["poetry>=0.12"]
build-backend = "poetry.masonry.api"

"""


SAMPLE_YAML = """\
name: bibimbap-env
dependencies:
  - python>=3.7,<4.0
  - foo>=0.2.3,<0.3.0
  - conda-forge::bar>=1.2.3,<2.0.0
  - thud>=1.4.5,<1.5.0
  - quux==2.34.5
  - quuz>=3.2
  - xyzzy>=2.1,<4.2
  - spinach>=19.10b0,<20.0
  - pizza>=1.2.3,<2.0.0    # Note that extra requirements are not supported on conda :-(
  - animals::lizard>=2.5.4,<3.0.0
  - pip
  - pip:
    - --index-url https://private.repo.my/my/stable/+simple/
    - --extra-index-url https://private.repo.my/my/edge/+simple/
    - baz>=0.4.5,<0.5.0
    - git+https://github.com/organization/repo.git@v2.7.4#egg=grault
"""

SAMPLE_YAML_EXTRA = """\
name: bibimbap-env
dependencies:
  - python>=3.7,<4.0
  - foo>=0.2.3,<0.3.0
  - conda-forge::bar>=1.2.3,<2.0.0
  - thud>=1.4.5,<1.5.0
  - quux==2.34.5
  - quuz>=3.2
  - xyzzy>=2.1,<4.2
  - spinach>=19.10b0,<20.0
  - pizza>=1.2.3,<2.0.0    # Note that extra requirements are not supported on conda :-(
  - animals::lizard>=2.5.4,<3.0.0
  - pudding>=1.0,<2.0
  - pip
  - pip:
    - --index-url https://private.repo.my/my/stable/+simple/
    - --extra-index-url https://private.repo.my/my/edge/+simple/
    - baz>=0.4.5,<0.5.0
    - git+https://github.com/organization/repo.git@v2.7.4#egg=grault
"""

SAMPLE_YAML_DEV = """\
name: bibimbap-env
dependencies:
  - python>=3.7,<4.0
  - foo>=0.2.3,<0.3.0
  - conda-forge::bar>=1.2.3,<2.0.0
  - thud>=1.4.5,<1.5.0
  - quux==2.34.5
  - quuz>=3.2
  - xyzzy>=2.1,<4.2
  - spinach>=19.10b0,<20.0
  - pizza>=1.2.3,<2.0.0    # Note that extra requirements are not supported on conda :-(
  - animals::lizard>=2.5.4,<3.0.0
  - fork>=1.2,<2.0
  - pip
  - pip:
    - --index-url https://private.repo.my/my/stable/+simple/
    - --extra-index-url https://private.repo.my/my/edge/+simple/
    - baz>=0.4.5,<0.5.0
    - git+https://github.com/organization/repo.git@v2.7.4#egg=grault
"""


def test_sample(tmpdir, mocker):
    toml_file = tmpdir / "pyproject.toml"
    yaml_file = tmpdir / "environment.yaml"

    with toml_file.open("w") as fd:
        fd.write(SAMPLE_TOML)
    expected = yaml.safe_load(io.StringIO(SAMPLE_YAML))

    mocker.patch("sys.argv", ["poetry2conda", str(toml_file), str(yaml_file)])
    main()

    with yaml_file.open("r") as fd:
        result = yaml.safe_load(fd)

    assert result == expected


def test_sample_extra(tmpdir, mocker):
    toml_file = tmpdir / "pyproject.toml"
    yaml_file = tmpdir / "environment.yaml"

    with toml_file.open("w") as fd:
        fd.write(SAMPLE_TOML)
    expected = yaml.safe_load(io.StringIO(SAMPLE_YAML_EXTRA))

    mocker.patch(
        "sys.argv", ["poetry2conda", str(toml_file), str(yaml_file), "-E", "dessert"]
    )
    main()

    with yaml_file.open("r") as fd:
        result = yaml.safe_load(fd)

    assert result == expected


def test_sample_dev(tmpdir, mocker):
    toml_file = tmpdir / "pyproject.toml"
    yaml_file = tmpdir / "environment.yaml"

    with toml_file.open("w") as fd:
        fd.write(SAMPLE_TOML)
    expected = yaml.safe_load(io.StringIO(SAMPLE_YAML_DEV))

    mocker.patch("sys.argv", ["poetry2conda", str(toml_file), str(yaml_file), "--dev"])
    main()

    with yaml_file.open("r") as fd:
        result = yaml.safe_load(fd)

    assert result == expected
