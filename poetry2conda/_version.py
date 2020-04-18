import warnings

import pkg_resources


def get_version():
    default = '0.0.0+unknown'
    try:
        distribution = pkg_resources.get_distribution('poetry2conda')
        return distribution.version
    except Exception as ex:
        warnings.warn(f'Could not determine poetry2conda version: {ex}', UserWarning)
        return default
