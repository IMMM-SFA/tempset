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


def get_example_htgsetp_params_file():
    """Convenience wrapper to retrieve file path from package data."""

    return pkg_resources.resource_filename('tempset', 'data/electric/htgsetp_params_electric.csv')


def get_example_clgsetp_file():
    """Convenience wrapper to retrieve file path from package data."""

    return pkg_resources.resource_filename('tempset', 'data/json/clgsetp_params.json')


def get_example_summary_file():
    """Convenience wrapper to retrieve file path from package data."""

    return pkg_resources.resource_filename('tempset', 'data/electric/summary.zip')


def get_example_idd_file():
    """Convenience wrapper to retrieve file path from package data."""

    return pkg_resources.resource_filename('tempset', 'data/eplus/Energy+.idd')


def get_example_electric_idf_file():
    """Convenience wrapper to retrieve file path from package data."""

    return pkg_resources.resource_filename('tempset', 'data/idf/electric.idf')


def get_example_gas_idf_file():
    """Convenience wrapper to retrieve file path from package data."""

    return pkg_resources.resource_filename('tempset', 'data/idf/gas.idf')


def get_example_main_idf_file():
    """Convenience wrapper to retrieve file path from package data."""

    return pkg_resources.resource_filename('tempset', 'data/idf/main.idf')
