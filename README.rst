============
poetry2conda
============

.. image:: https://img.shields.io/pypi/v/poetry2conda.svg
    :target: https://pypi.org/project/poetry2conda/
.. image:: https://img.shields.io/pypi/l/poetry2conda.svg
    :target: https://pypi.org/project/poetry2conda/

A script to convert a Python project declared on a pyproject.toml to a conda
environment.

This is not an attempt to move away from pyproject.toml to conda. It is a tool
to help teams maintain a single file for dependencies when there are
collaborators that prefer regular Python/PyPI and others that prefer conda.

Features
--------

- Set conda channels for each dependency.
- Rename conda dependencies.
- Convert tilde and caret dependencies to regular version specifiers.
- Handle pure pip dependencies.

Installation
------------

You will be able to install poetry2conda by running:

.. code-block:: bash

    $ pip install poetry2conda

Usage
-----

The most straightforward use-case for poetry2conda is to convert a pyproject.toml
that uses poetry. This can be achieved by adding the following section to your
pyproject.toml:

.. code-block:: toml

    [tool.poetry.dependencies]
    foo = "^1.2.3"
    # ...

    [tool.poetry2conda]
    name = "some-name-env"

Then, use the command line to create a conda environment file:

.. code-block:: bash

    $ poetry2conda pyproject.toml environment.yaml

    # or if you want to see the contents but not write the file:
    $ poetry2conda pyproject.toml -

This will create a yaml file like:

.. code-block:: yaml

    name: some-name-env
    dependencies:
      - foo>=1.2.3,<2.0.0
      # ...

Sometimes, a dependency is handled differently on conda. For this case,
the section ``tool.poetry2conda.dependencies`` can be used to inform on specific
channels, or package names.

For example, if a dependency should be installed from a specific channel, like
conda-forge, declare it as follows:


.. code-block:: toml

    [tool.poetry.dependencies]
    foo = "^1.2.3"
    # ...

    [tool.poetry2conda]
    name = "my-env-with-channels"

    [tool.poetry2conda.dependencies]
    foo = { channel = "conda-forge" }

After conversion, the yaml file will look like:

.. code-block:: yaml

    name: my-env-with-channels
    dependencies:
      - conda-forge::foo>=1.2.3,<2.0.0
      # ...

Sometimes, a package on PyPI does not have the same name on conda
(why? why not? confusion!). For example, ``tables`` and ``pytables``,
``docker`` and ``docker-py``. To change the name when converting to a conda
environment file, you can set it as:

.. code-block:: toml

    [tool.poetry.dependencies]
    docker = "^4.2.0"
    # ...

    [tool.poetry2conda]
    name = "another-example"

    [tool.poetry2conda.dependencies]
    docker = { name = "docker-py" }

The converted yaml file will look like:

.. code-block:: yaml

    name: another-example
    dependencies:
      - docker-py>=4.2.0,<5.0.0
      # ...

When a package does not exist on conda, declare it on the pip channel:

.. code-block:: toml


    [tool.poetry.dependencies]
    quetzal-client = "^0.5.2"
    # ...

    [tool.poetry2conda]
    name = "example-with-pip"

    [tool.poetry2conda.dependencies]
    quetzal-client = { channel = "pip" }

Which would give:

.. code-block:: yaml

    name: example-with-pip
    dependencies:
      - pip
      - pip:
        - quetzal-client>=0.5.2,<0.6.0


Not all poetry dependency types are supported, only regular ones and git
dependencies:

.. code-block:: toml


    [tool.poetry.dependencies]
    my_private_lib = { git = "https://github.com/company/repo.git", tag = "v1.2.3" }
    # ...

    [tool.poetry2conda]
    name = "example-with-git"

This is handled like a pure pip dependency:

.. code-block:: yaml

    name: example-with-git
    dependencies:
      - pip
      - pip:
        - git+https://github.com/company/repo.git@v1.2.3#egg=my_private_lib

Packages with extras are supported on a pyproject.toml, but conda does not
support extras. For the moment, this information is dropped:

.. code-block:: toml


    [tool.poetry.dependencies]
    dask = { extras = ["bag"], version = "^2.15.0" }
    # ...

    [tool.poetry2conda]
    name = "example-with-extras"

Which will be translated to:

.. code-block:: yaml

    name: example-with-extras
    dependencies:
      - dask>=2.15.0,<3.0.0

Sometimes (very rarely) a package is not available on PyPI but conda does have
a it. Poetry can handle this with a git dependency and poetry2conda can keep
these as pip installable packages. But if you prefer to transform it to its
conda package, use the following configuration:

.. code-block:: toml

    [tool.poetry.dependencies]
    weird = { git = "https://github.com/org/weird.git", tag = "v2.3" }

    [tool.poetry2conda]
    name = "strange-example"

    [tool.poetry2conda.dependencies]
    weird = { name = "bob", channel = "conda-forge", version = "^2.3" }  # You need to declare the version here

Which will be translated to:

.. code-block:: yaml

    name: strange-example
    dependencies:
      - conda-forge::bob>=2.3.0,<3.0.0


If you want to include the dev-dependencies in the generated conda
environment file, you can pass the `--dev` option to poetry2conda.  All
the caveats and conversion patches that are described above apply to
dev dependencies all the same.


Contribute
----------

- Issue Tracker: https://github.com/dojeda/poetry2conda/issues
- Source Code: https://github.com/dojeda/poetry2conda


License
-------

The project is licensed under the BSD license.



Why poetry2conda?
-----------------

This part is an opinion.

Python is a great language with great libraries, but environment management has
been notoriously bad. Bad enough to have its own `XKCD comic <https://xkcd.com>`_:

.. image:: https://imgs.xkcd.com/comics/python_environment.png
  :alt: Python environment bankrupcty.
  :width: 50%
  :align: center

There is a lack of agreement on how and where to declare dependencies.
``setup.py`` contains abstract dependencies (but only apply to packages), and
``requirements.txt`` file has concrete dependencies
(with version specifications). But development dependencies go somewhere else in
``requirements-dev.txt`` and testing dependencies in ``requirements-test.txt``.
Because dependencies are now declared in two or more
separate files, this is a burden. Some people read and parse ``requirements-*.txt``
files on their ``setup.py``. Others say that this is a bad practice.

Then, there is the environment management problem. ``virtualenv`` was created a
long time ago to isolate environments so you one does end up with the
dependencies of another project. I do not know why, this was not enough,
``venv`` was created. And then some other ones that can handle different Python
versions.

At some point on this story, a new generation of clever developers brought
ideas from other package managers to improve on how packages, environments, etc.
should be managed. ``requirements.txt`` were replaced (in theory) by
``Pipfile`` and ``Pipfile.lock``. New tools were created to manage packages and
environments, such as Pipenv and poetry, tackling even more problems such as
virtual environments, Python versions, and many other distribution problems.

Dependencies, environemnts, package managers... this confused a lot of people
(including me).

Eventually, I decided to give the
`PEP 5128 <https://www.python.org/dev/peps/pep-0518/>`_ and poetry a try.
It was not easy: a new markup language, TOML (Tom's Obvious Markup Language,
which has this strange old man smell, like naphtalene, because it looks like
a new INI file). I encountered many new problems with poetry.
I abandoned many times but always came back because at least it helps me
define my dependencies in only file. After two or three tries, I decided to
migrate my code base to poetry and drop the requirement and setup files.

But wait...

To add a bit of entropy to the Python situation, a company called Continuum
Analytics (later renamed Anaconda) created a *different* Python distribution a
nd package management, Anaconda (and its less obese brother, Miniconda).
I think they were tired of the current Python situation, and they were right.
They replaced all of the virtual environment problems with their own
environments and they distribute their own packages without using the current
Python package authority, PyPI. This worked
well, in my opinion, because Anaconda distributes compiled versions of some
packages, giving massive performance improvements in some cases (like NumPy),
because it is easier to setup on Windows,
but more importantly because Anaconda was targeted for the
*scientific computing community* (e.g. data scientists).

Cool! I should migrate to conda then! Alas, some people (like me),
who used Python before Anaconda ever existed, tried it and got confused.

I have three main problems with conda: First, not all packages are distributed
by Anaconda, so you eventually need to mix conda and pip to work together. It is
difficult to summarize how many problems I have encountered when mixing these
two. Second, every single day I use conda, I ran into problems: maybe something
was installed on the root environment (this also happens without conda),
maybe I wrote a command the wrong way (errors are often misleading),
maybe the command syntax changed recently,
maybe my network is slow and that explains why adding a new dependency takes
ages (among other examples). I can go on. Third, I said to myself, if you are
going to use conda, you should go all the way and write packages for their conda
repositories. Oh boy, I tried
that and it is very complicated and the documentation is so confusing.
I eventually managed to do it, but I have PTSD.

So to summarize, I am not convinced by Anaconda, buy I have colleagues or
collaborators that do use it. I don't understand why (yes, apparently tensorflow
is faster with anaconda, sigh...). But I have to admit that conda is not going
to go anywhere.

This leaves me in an uncomfortable situation: I want to use poetry, but I don't
like forcing others to use it to. And by others I mean my conda friends. I
searched for some tool to auto-convert from one to another. Dephell does this,
but it does not address all of my use-cases. There is an open issue for some
of them. I saw that changing dephell was going to be a complicated endeavor,
so I decided to just write a new tool to do it.

So that's why poetry2conda exists.
