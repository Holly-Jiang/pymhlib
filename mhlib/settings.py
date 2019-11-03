"""
Provides configuration file and command line argument parsing functionality to all modules.

Parameters can be decentrally defined in any module by getting the global parser via get_settings_parser
and registering them by add_argument(). parse_settings() needs to be called one in the main program, then
all parameters are available under the global Namespace settings.
If sys.argv shall not be used, e.g., because pymhlib is embedded in some framework like Django or
a Jupyter notebook, pass "" as args (or some meaningful initialization parameters).

For the usage of config files see the documentation of configargparse or call the program with -h.
"""

import pickle
import numpy as np
import random
from configargparse import ArgParser, Namespace, ArgumentDefaultsRawHelpFormatter


settings = Namespace()  # global Namespace with all settings
unknown_args = []  # global list with all unknown parameters
_parser = None  # single global settings parser


def get_settings_parser() -> ArgParser:
    """Returns the single global argument parser for adding parameters.

    Parameters can be added in all modules by add_argument.
    After calling parse() once in the main program, all settings
    are available in the global settings dictionary.
    """
    global _parser
    if not _parser:
        _parser = ArgParser(  # default_config_files=["default.cfg"],
                                           formatter_class=ArgumentDefaultsRawHelpFormatter)
        _parser.set_defaults(seed=0)
    return _parser


def add_bool_arg(parser: ArgParser, name: str, default: bool, **kwargs):
    """Add a boolean parameter to the settings parser.

    This helper function add two arguments "--"+name and "--no-"+name to the settings parser for a boolean parameter.

    :param parser: parser obtained by get_settings_parser
    :param name: name of the parameter without "--"
    :param default: default value
    :param kwargs: further parameters such as help
    """
    parser.add_argument('--' + name, dest=name, action='store_true', default=default, **kwargs)
    parser.add_argument('--no-' + name, dest=name, action='store_false')


def parse_settings(args=None, return_unknown=False, default_config_files=None):
    """Parses the config files and command line arguments and initializes settings and unknown_parameters.

    Needs to be called once in the main program, or more generally after all arguments have been added to the parser
    and before they are used.
    Also seeds the random number generators based on parameter seed.
    If sys.argv shall not be used, e.g., because pymhlib is embedded in some framework like Django or
    a Jupyter notebook, pass "" as args (or some meaningful initialization parameters).

    :param args: optional sequence of string arguments; if None sys.argv is used
    :param return_unknown: return unknown parameters as list in global variable unknown_args; otherwise raise exception
    :param default_config_files: list of default config files to read
    """
    global settings, unknown_args
    p = get_settings_parser()
    p.add_argument('--seed', type=int, help='seed for the random number generators (0: random init)')
    p.add_argument('-c', '--config', is_config_file=True, help='config file to be read')
    p._default_config_files = default_config_files if default_config_files else []
    if return_unknown:
        _, unknown_args[:] = p.parse_known_args(args=args, namespace=settings)
    else:
        p.parse_args(args=args, namespace=settings)

    seed_random_generators()


def set_settings(s: Namespace):
    """Adopt given settings.

    Used, for example in child processes to adopt settings from parent process.
    """
    settings.__dict__ = s.__dict__
    seed_random_generators()


def seed_random_generators():
    """Initialize random number generators with settings.seed. If zero, a random seed is generated."""
    if settings.seed == 0:
        np.random.seed()
        settings.seed = np.random.randint(np.iinfo(np.int32).max)
    np.random.seed(settings.seed)
    random.seed(settings.seed)


def save_settings(filename):
    """Save settings to given binary file."""
    with open(filename, 'wb') as f:
        pickle.dump(settings, f, pickle.HIGHEST_PROTOCOL)


def load_settings(filename):
    """Load settings from given binary file."""
    with open(filename, 'rb') as f:
        global settings
        settings.__dict__ = vars(pickle.load(f))
        seed_random_generators()


def get_settings_as_str():
    """Get all parameters and their values as descriptive multi-line string."""
    s = "\nsettings:\n"
    for key, value in sorted(vars(settings).items()):
        s += f"{key}={value}\n"
    return s


class OwnSettings:
    """An individualized settings storage, which falls back to the default setting for not provided parameters."""

    def __init__(self, own_settings: dict = None):
        self.__dict__ = own_settings if own_settings else dict()

    def __getattr__(self, item):
        try:
            return self.__dict__[item]
        except KeyError:
            val = settings.__getattribute__(item)
            self.__setattr__(item, val)
            return val
