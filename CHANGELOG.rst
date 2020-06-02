=========
Changelog
=========

This document lists all important changes to poetry2conda.

Version numbers follow `semantic versioning <http://semver.org>`_.

0.3.0 (2020-06-02)
------------------

Thanks to @abergeron for contributing!

* #3 Fix support for dependencies that do not follow semantic version.
* #1 Fix incorrect file creation when command fails.
* Add support for `poetry extras <https://python-poetry.org/docs/pyproject/#extras>`_.
* Add option to include development dependencies.
* Add automated unit tests on github.

0.2.0 (2020-05-04)
------------------

* Add minimal support for extras, which are dropped on the conda environment.

0.1.0 (2020-04-28)
------------------

* Initial release.
