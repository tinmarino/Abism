"""
    Util functions
"""

# Standard
import sys
import os
from os.path import dirname, abspath
from functools import lru_cache


# Local
from abism import __version__


_verbose = 10  # Verbose level
_parsed_args = None  # Arguments from argparse

# Keep a trace
# this global removes others
_root = None


def parse_argument():
    from argparse import ArgumentParser
    from sys import argv
    parser = ArgumentParser(description='Adaptive Background Interferometric Strehl Meter')

    # Image
    parser.add_argument(
        '-i', '--image', metavar='image.fits', type=str,
        action='append',
        help='image to diplay: filepath of the .fits')

    parser.add_argument(
        'image', metavar='image.fits', type=str,
        default='',
        nargs='?', action='append',
        help='image to diplay: the first one is chosen')

    parser.add_argument(
        '-v', '--verbose', type=int,
        default=0, action='store',
        help='verbosity level: 0..10')


    # Custom
    parsed_args = parser.parse_args()
    log(3, 'Parsed initially:', parsed_args)
    parsed_args.script = argv[0]
    parsed_args.image = parsed_args.image[0]

    # set
    global _parsed_args, verbose
    _parsed_args = parsed_args
    _verbose = _parsed_args.verbose


def get_colormap_list():
    """Favorite colormap of Tinmarino (me)
    Link: https://matplotlib.org/examples/color/colormaps_reference.html
    Perceptually Uniform Sequential:
        magma       <- the (3) others have a high too yellow (
    Diverging:
        RdYlBlu     <- high contrast (need one), more than Spectral
        PrGn        <- diffrent: 2 colors: no blue, rew, black, white
    Miscellanous:
        cubehelix   <- enhanced B&W (with some pink, greeny blue) awesome!

    """
    import matplotlib as mpl

    # Register solarized
    cmap_solarized = mpl.colors.LinearSegmentedColormap.from_list(
        'solarized',
        ['#6c71c4',
         '#268bd2',
         '#859900',
         '#b58900',
         '#cb4b16',
         '#dc322f'])
    mpl.cm.register_cmap(name='solarized', cmap=cmap_solarized)

    return [
        ['Black&White', 'bone'],
        ['Solarized', 'solarized'],
        ['Spectral-r', 'Spectral_r'],
        ['Magma', 'magma'],
        ['Cubehelix', 'cubehelix'],
        ['RdYlBu_r', 'RdYlBu_r'],
        ['PRGn', 'PRGn'],
        ]






class AbismState:
    """Confiugration from user (front) to science (back)"""
    def __init__(self):
        """Radio button state
        What is the user asking for ?
        """
        # Type
        self.fit_type = 'Moffat2D'
        self.pick_type = 'one'
        self.phot_type = 'elliptical_aperture'
        self.noise_type = 'elliptical_annulus'
        self.aperture_type = 'fit'
        self.pick_old = ''

        # More
        self.b_aniso = True
        self.b_same_psf = True
        self.b_same_center = True

        # UI
        self.b_see_more = False  # See more frame ?
        self.b_see_manual_background = False  # See manual background
        self.s_image_color_map = 'bone'

@lru_cache(1)
def get_state():
    return AbismState()


def get_root():
    return _root


def set_root(root):
    global _root; _root = root


def quit_process():
    """Kill process"""
    log(1, 'Closing Abism, Goodbye. Come back soon.' + "\n" + 100 * '_' + 3 * "\n")
    # parent.destroy()
    sys.exit(0)


def restart():
    """ TODO move me to Global Definer, WritePref and ReadPref
        Pushing this button will close ABISM and restart it the same way it was launch before.
        Programmers: this is made to reload the Software if a modification in the code were made.
    """

    ###########
    # PREPARE STG command line args
    stg = 'python ' + _parsed_args.script + ' '
    arg_dic = vars(_parsed_args)
    for key, value in arg_dic.items():
        if key == 'script' or not value: continue
        print(key, ' ', arg_dic[key])
        stg += '--' + key + ' ' + str(value) + ' '
    stg += '&'
    log(0, "\n\n\n" + 80 * "_" + "\n",
        "Restarting ABISM with command:\n" + stg + "\nplease wait")

    ##########
    # DESTROY AND LAUNCH
    get_root().destroy()  # I destroy Window,
    os.system(stg)         # I call an other instance
    sys.exit(0)         # I exit the current process.
    # As the loop is now opened, this may not be necessary but anyway it is safer


def get_version():
    """Return: version string"""
    return __version__


def get_verbose():
    """Return verbose module variable"""
    return _verbose


def set_verbose(i_level):
    """Set verbose module variable"""
    _verbose = i_level
    return _verbose


@lru_cache(1)
def root_path():
    """Return: path of this file"""
    return dirname(abspath(__file__)) + '/'


@lru_cache(1)
def _get_logger():
    import logging
    # Logger
    logFormatter = logging.Formatter(
        'ABISM: %(asctime)-8s: %(message)s',
        '%H:%M:%S')

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO)
    consoleHandler.setFormatter(logFormatter)

    logger = logging.getLogger('ABISM')
    logger.setLevel(logging.INFO)
    logger.handlers = [consoleHandler]

    return logger


def log(i, *args):
    """Log utility read verbose"""
    if get_verbose() < i: return

    message = str(i) + ': ' + ' '.join([str(arg) for arg in args])
    _get_logger().info(message)
