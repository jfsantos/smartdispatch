from __future__ import absolute_import

import os
import re
import itertools
from datetime import datetime

import smartdispatch
from smartdispatch import utils
from smartdispatch.argument import EnumerationFoldedArgument, RangeFoldedArgument

UID_TAG = "{UID}"


def generate_name_from_command(command, max_length_arg=None, max_length=None):
    ''' Generates name from a given command.

    Generate a name by replacing spaces in command with dashes and
    by trimming lengthty (as defined by max_length_arg) arguments.

    Parameters
    ----------
    command : str
        command from which to generate the name
    max_length_arg : int
        arguments longer than this will be trimmed keeping last characters (Default: inf)
    max_length : int
        trim name if longer than this keeping last characters (Default: inf)

    Returns
    -------
    name : str
        slugified name
    '''
    if max_length_arg is not None:
        max_length_arg = min(-max_length_arg, max_length_arg)

    if max_length is not None:
        max_length = min(-max_length, max_length)

    name = '_'.join([utils.slugify(argvalue)[max_length_arg:] for argvalue in command.split()])
    return name[max_length:]


def generate_name_from_arguments(arguments, max_length_arg=None, max_length=None, prefix=datetime.now().strftime('%Y-%m-%d_%H-%M-%S_')):
    ''' Generates name from given unfolded arguments.

    Generate a name by concatenating the first and last values of every
    unfolded arguments and by trimming lengthty (as defined by max_length_arg)
    arguments.

    Parameters
    ----------
    arguments : list of list of str
        list of unfolded arguments
    max_length_arg : int
        arguments longer than this will be trimmed keeping last characters (Default: inf)
    max_length : int
        trim name if longer than this keeping last characters (Default: inf)
    prefix : str
        text to preprend to the name (Default: current datetime)

    Returns
    -------
    name : str
        slugified name
    '''
    if max_length_arg is not None:
        max_length_arg = min(-max_length_arg, max_length_arg)

    if max_length is not None:
        max_length = min(-max_length, max_length)

    name = []
    for argvalues in arguments:
        argvalues = map(utils.slugify, argvalues)
        name.append(argvalues[0][max_length_arg:])
        if len(argvalues) > 1:
            name[-1] += '-' + argvalues[-1][max_length_arg:]

    name = "_".join(name)

    name = prefix + name[max_length:]
    return name


def get_commands_from_file(fileobj):
    ''' Reads commands from `fileobj`.

    Parameters
    ----------
    fileobj : file
        opened file where to read commands from

    Returns
    -------
    commands : list of str
        commands read from the file
    '''
    return fileobj.read().strip().split('\n')


def get_commands_from_arguments(arguments):
    ''' Obtains commands from the product of every unfolded arguments.
    Parameters
    ----------
    arguments : list of list of str
        list of unfolded arguments
    Returns
    -------
    commands : list of str
        commands resulting from the product of every unfolded arguments
    '''
    return ["".join(argvalues) for argvalues in itertools.product(*arguments)]


def unfold_arguments(arguments):
    ''' Unfolds folded arguments into a list of unfolded arguments.

    An argument can be folded e.g. a list of unfolded arguments separated by commas.
    An unfolded argument unfolds to itself.

    Parameters
    ----------
    arguments : list of str
        arguments to unfold

    Returns
    -------
    unfolded_arguments : list of str
        result of the unfolding

    Complex arguments
    -----------------
    *enumeration*: "[item1 item2 ... itemN]"
    *range*: "[start:end]" or "[start:end:step]"
    '''
    text = utils.escape(" ".join(arguments))

    # Order matter, if some regex is more greedy than another, the it should go after
    arguments = [RangeFoldedArgument(), EnumerationFoldedArgument()]

    # Build the master regex with all argument's regex
    regex = "(" + "|".join(["(?P<{0}>{1})".format(arg.name, arg.regex) for arg in arguments]) + ")"

    pos = 0
    unfolded_arguments = []
    for match in re.finditer(regex, text):
        # Add already unfolded argument
        unfolded_arguments.append([text[pos:match.start()]])

        # Unfold argument
        groupdict = match.groupdict()
        for argument in arguments:
            if groupdict[argument.name] is not None:
                unfolded_arguments.append(argument.unfold(groupdict[argument.name]))

        pos = match.end()

    unfolded_arguments.append([text[pos:]])  # Add remaining unfolded arguments
    unfolded_arguments = [map(utils.hex2str, argvalues) for argvalues in unfolded_arguments]
    return unfolded_arguments


def replace_uid_tag(commands):
    return [command.replace("{UID}", utils.generate_uid_from_string(command)) for command in commands]


def get_available_queues(cluster_name=utils.detect_cluster()):
    """ Fetches all available queues on the current cluster """
    if cluster_name is None:
        return {}

    smartdispatch_dir, _ = os.path.split(smartdispatch.__file__)
    config_dir = os.path.join(smartdispatch_dir, 'config')

    config_filename = cluster_name + ".json"
    config_filepath = os.path.join(config_dir, config_filename)

    if not os.path.isfile(config_filepath):
        return {}  # Unknown cluster

    queues_infos = utils.load_dict_from_json_file(config_filepath)
    return queues_infos
