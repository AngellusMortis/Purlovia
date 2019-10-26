'''
Utilities for easy cache file usage.

'''
import hashlib
import json
import pickle
import tempfile
from collections.abc import Hashable
from logging import NullHandler, getLogger
from pathlib import Path
from typing import *

from ue.utils import property_serialiser

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def cache_data(key: object, filename: str, generator_fn: Callable[[object], object], force_regenerate=False):
    '''
    Manage cacheable data.
    Will return cached data if it exists and its hash matches that of the given key, else will call the generator
    function, save it to a cache file and return the result.

    `key` is a JSON-serialisable object specifying any versions needed to uniquely identify the data.
    `filename` is a name to use for the temp file.
    `generator_fn` is a (usually slow) function to generate the data that would otherwise be cached. This function will be passed the `key` object.
    `force_regenerate` to ignore existing cached data and always regerenate it.

    Example usage:
        key = { 'version': 1, 'lastModified': 34785643526 }
        data = cached_data(key, 'filename', generate_the_data)
    '''
    basepath: Path = Path(tempfile.gettempdir()) / filename
    data_filename = basepath.with_suffix('.pickle')
    hash_filename = basepath.with_suffix('.hash')
    key_hash = _hash_from_object(key)

    # Try to find hash of cached file, if it exists
    existing_hash: str = ''
    if not force_regenerate:
        try:
            with open(hash_filename, 'rt') as f:
                existing_hash = f.read().strip()
        except IOError:
            logger.debug(f'Cached hash file {hash_filename} could not be loaded')

    # If they match, load and return the cached data
    if key_hash == existing_hash:
        try:
            with open(data_filename, 'rb') as f:
                logger.debug(f'Re-using existing cached data')
                data = pickle.load(f)
                return data
        except IOError:
            logger.warning(f'Cached data file {data_filename} is missing and must be regenerated')
        except pickle.PickleError:
            logger.warning(f'Cached data file {data_filename} could not be unpickled and must be regenerated')
    else:
        logger.debug(f'Hash did not match')

    # Generate new data, hash it, and save it for future use
    logger.debug(f'Triggering data generation')
    data = generator_fn(key)

    try:
        with open(hash_filename, 'wt') as f:
            f.write(key_hash)
    except IOError:
        logger.exception(f'Unable to save cached data hash file {hash_filename}')

    try:
        with open(data_filename, 'wb') as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    except IOError:
        logger.exception(f'Unable to save cached data in {hash_filename}')

    return data


def _hash_from_object(key: object) -> str:
    json_string = json.dumps(key, default=property_serialiser, indent=None, separators=(',', ':'))
    as_bytes = json_string.encode('utf8')
    digest = hashlib.sha512(as_bytes).hexdigest()
    return "sha512:" + digest