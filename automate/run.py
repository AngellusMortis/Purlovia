import argparse
import logging
import logging.config
import os
from pathlib import Path
from typing import *

import yaml

from config import ConfigFile, get_global_config

from .ark import ArkSteamManager
from .export import export_values
from .git import GitManager
from .manifest import update_manifest

# pylint: enable=invalid-name

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
logger.addHandler(logging.NullHandler())


def setup_logging(path='config/logging.yaml', level=logging.INFO):
    '''Setup logging configuration.'''
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=level)

    logging.captureWarnings(True)

    root_logger = logging.getLogger()
    logging.addLevelName(100, 'STARTUP')
    root_logger.log(100, '')
    root_logger.log(100, '-' * 100)
    root_logger.log(100, '')


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Perform an automated run of Purlovia")

    parser.add_argument('--dev', action='store_true', help='Enable dev mode [skips install, commit and push]')

    parser.add_argument('--skip-install', action='store_true', help='Skip instllation of game and mods')
    parser.add_argument('--skip-extract', action='store_true', help='Skip extracting all species')
    parser.add_argument('--skip-vanilla', action='store_true', help='Skip extracting vanilla species')
    parser.add_argument('--skip-commit', action='store_true', help='Skip committing to Git (uses dry-run mode)')
    parser.add_argument('--skip-push', action='store_true', help='Skip pushing to Git')

    parser.add_argument('--stats', action='store', choices=('8', '12'), help='Specify the stat format to export')

    parser.add_argument('--log-dir', action='store', type=Path, default=Path('logs'), help="Change the default logging level")

    return parser


def handle_args(args: Any) -> ConfigFile:
    # Ensure log directory exists before starting the logging system
    args.log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(path='config/logging.yaml')

    if args.dev:
        args.skip_commit = True
        args.skip_install = True
        logger.info('DEV mode enabled')

    config = get_global_config()

    if args.stats:
        if int(args.stats) == 12:
            config.settings.Export8Stats = False
        else:
            config.settings.Export8Stats = True

    if args.skip_install:
        config.settings.SkipInstall = True

    if args.skip_extract:
        config.settings.SkipExtract = True

    if args.skip_vanilla:
        config.settings.ExportVanillaSpecies = False

    if args.skip_commit:
        config.settings.SkipCommit = True

    if args.skip_push:
        config.settings.SkipPush = True

    return config


def run(config: ConfigFile):

    # Run update then export
    try:
        # Get mod list
        mods = config.mods

        # Update game ad mods
        arkman = ArkSteamManager(config=config)
        arkman.ensureSteamCmd()
        arkman.ensureGameUpdated()
        arkman.ensureModsUpdated(mods)

        # Ensure Git is setup and ready
        git = GitManager(config=config)
        git.before_exports()

        # Export vanilla and/or requested mods
        export_values(arkman, set(mods), config)

        # Update the manifest file
        update_manifest(config=config)

        # Commit any changes
        git.after_exports()

        logger.info('Automation completed')

    except:  # pylint: disable=bare-except
        logger.exception('Caught exception during automation run. Aborting.')


def main():
    parser = create_parser()
    args = parser.parse_args()
    config = handle_args(args)
    run(config)
