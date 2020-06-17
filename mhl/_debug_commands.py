"""
__author__ = "Patrick Renner, Alexander Sahm"
__copyright__ = "Copyright 2020, Pomfort GmbH"

__license__ = "MIT"
__maintainer__ = "Patrick Renner, Alexander Sahm"
__email__ = "opensource@pomfort.com"
"""
import os
import shutil

import click
from .commands import seal_file_path, commit_session
from .generator import MHLGenerationCreationSession
from . import logger
from . import history_fs_backend
from .chain_txt_backend import MHLChainTXTBackend
from . import hashlist_xml_parser
from .traverse import post_order_lexicographic
from .__version__ import ascmhl_supported_hashformats, ascmhl_folder_name


@click.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def readchainfile(filepath, verbose):
    """
    read an ASC-MHL file
    """

    chain = MHLChainTXTBackend.parse(filepath)

    if verbose:
        chain.log()


@click.command()
@click.argument('filepath', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def readmhlfile(filepath, verbose):
    """
    read an ASC-MHL file
    """

    hashlist = hashlist_xml_parser.parse(filepath)

    if verbose:
        hashlist.log()


@click.command()
@click.argument('root_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
def readmhlhistory(root_path, verbose):
    """
    read an ASC-MHL file
    """

    history = history_fs_backend.parse_history(root_path)

    if verbose:
        history.log()


@click.command()
@click.argument('root_path', type=click.Path(exists=False))
def create_dummy_file_structure(root_path):
    """
    create a potentially huge set of dummy files to test how the commands can handle large file systems
    """

    folder_depth = 3
    print('delete old dummy folder')
    dummy_folder = os.path.join(root_path, 'dummy_fs')
    if os.path.exists(dummy_folder):
        shutil.rmtree(dummy_folder)
    os.makedirs(dummy_folder, exist_ok=True)
    create_dummy_folder(dummy_folder, '', folder_depth)


def create_dummy_folder(root_path, prefix, depth):
    num_folders = 10
    num_files = 200
    verbose = False
    if len(prefix) > 0:
        folder_path = os.path.join(root_path, prefix)
        print(f'd: {folder_path}')
        os.mkdir(folder_path)
        for file in range(0, num_files):
            file_name = f'{prefix}{file:03}.txt'
            file_path = os.path.join(folder_path, file_name)
            if verbose:
                print(f'f: {file_path}')
            with open(file_path, 'w') as file_handle:
                file_handle.write(file_name)
    else:
        folder_path = root_path
    if depth == 0:
        return
    for folder in range(0, num_folders):
        folder_name = prefix + chr(ord('A') + folder)
        create_dummy_folder(folder_path, folder_name, depth-1)


@click.command()
@click.argument('root_path', type=click.Path(exists=True))
@click.argument('paths', type=click.Path(exists=True), nargs=-1)
@click.option('--verbose', '-v', default=False, is_flag=True, help="Verbose output")
@click.option('--hash_format', '-h', type=click.Choice(ascmhl_supported_hashformats), multiple=False,
              default='xxh64', help="Algorithm")
def verify_paths(root_path, paths, verbose, hash_format):
    """
    read an ASC-MHL file
    """
    logger.verbose_logging = verbose

    if not os.path.isabs(root_path):
        root_path = os.path.join(os.getcwd(), root_path)

    existing_history = history_fs_backend.parse_history(root_path)
    # start a verification session on the existing history
    session = MHLGenerationCreationSession(existing_history)

    for path in paths:
        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)
        if os.path.isdir(path):
            for folder_path, children in post_order_lexicographic(path, ['.DS_Store', ascmhl_folder_name]):
                for item_name, is_dir in children:
                    file_path = os.path.join(folder_path, item_name)
                    if is_dir:
                        continue
                    seal_file_path(existing_history, file_path, hash_format, session)
        else:
            seal_file_path(existing_history, path, hash_format, session)

    commit_session(session)

    if verbose:
        existing_history.log()
