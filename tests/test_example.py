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

[tool.poetry.dependencies]
python = "^3.7"
foo = "^0.2.3"              # Example of a caret requirement whose major version is zero
bar = "^1.2.3"              # Example of a caret requirement whose major version is not zero
baz = "~0.4.5"              # Example of a tilde requirement whose major version is zero
qux = "~1.4.5"              # Example of a tilde requirement whose major version is not zero
quux = "2.34.5"             # Example of an exact version
quuz = ">=3.2"              # Example of an inequality
xyzzy = ">=2.1,<4.2"        # Example of two inequalities
grault = { git = "https://github.com/organization/repo.git", tag = "v2.7.4"}   # Example of a git package

[tool.poetry2conda]
name = "bibimbap-env"

[tool.poetry2conda.dependencies]
bar = { channel = "conda-forge" }            # Example of a package on conda-forge
baz = { channel = "pip" }                    # Example of a pure pip package
qux = { name = "thud" }                      # Example of a package that changes names in conda

[build-system]
requires = ["poetry>=0.12"]
build-backend = "poetry.masonry.api"

"""


SAMPLE_YAML = """\
name: bibimbap-env
dependencies:
  - python>=3.7.0,<4.0.0
  - foo>=0.2.3,<0.3.0
  - conda-forge::bar>=1.2.3,<2.0.0
  - thud>=1.4.5,<1.5.0
  - quux==2.34.5
  - quuz>=3.2.0
  - xyzzy>=2.1.0,<4.2.0
  - pip
  - pip:
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
