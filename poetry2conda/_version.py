import pathlib
import warnings

import toml


def get_version():
    path = pathlib.Path(__file__).parents[1] / 'pyproject.toml'
    default = '0.0.0+unknown'
    if not path.exists():
        return default

    try:
        with path.open('r') as f:
            config = toml.load(f)

        version = config['tool']['poetry']['version']
        return version

    except Exception as ex:
        warnings.warn(f'Could not determine poetry2conda version: {ex}', UserWarning)
        return default
