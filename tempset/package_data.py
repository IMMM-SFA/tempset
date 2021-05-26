import pkg_resources


def get_example_eplus_file():
    """Convenience wrapper to retrieve file path from package data."""

    return pkg_resources.resource_filename('tempset', 'data/json/eplus_params.json')


def get_example_batch_file():
    """Convenience wrapper to retrieve file path from package data."""

    return pkg_resources.resource_filename('tempset', 'data/json/batch_params.json')


def get_example_htgsetp_file():
    """Convenience wrapper to retrieve file path from package data."""

    return pkg_resources.resource_filename('tempset', 'data/json/htgsetp_params.json')
