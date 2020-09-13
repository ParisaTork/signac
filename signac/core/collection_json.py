# Copyright (c) 2020 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""Implements JSON-backend.

This implements the JSON-backend for SyncedCollection API by
implementing sync and load methods.
"""

import os
import json
import errno
import uuid
import hashlib
import logging
import warnings

from .synced_collection import SyncedCollection
from .syncedattrdict import SyncedAttrDict
from .synced_list import SyncedList
from .buffers import FileBuffer
from .synced_collection import _register_buffered_backend
from .synced_collection import _in_buffered_mode
from .validators import json_format_validator


logger = logging.getLogger(__name__)


def _convert_key_to_str(data):
    """Recursively convert non-string keys to strings for (potentially nested) input collections.

    This retains compatibility with auto-casting keys to strings, and will be
    removed in signac 2.0.
    Input collections must be of "base type" (dict or list).
    """
    if isinstance(data, dict):
        def _str_key(key):
            if not isinstance(key, str):
                warnings.warn(f"Use of {type(key).__name__} as key is deprecated "
                              "and will be removed in version 2.0",
                              DeprecationWarning)
                key = str(key)
            return key
        return {_str_key(key): _convert_key_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_convert_key_to_str(value) for value in data]
    return data


class JSONCollection(SyncedCollection, FileBuffer):
    """Implement sync and load using a JSON back end."""

    _backend = __name__  # type: ignore

    def __init__(self, filename=None, write_concern=False, **kwargs):
        self._filename = None if filename is None else os.path.realpath(filename)
        self._write_concern = write_concern
        kwargs['name'] = filename
        super().__init__(**kwargs)
        self._supports_buffering = True

    def _load_from_file(self):
        """Load the data from a JSON file."""
        try:
            with open(self._filename, 'rb') as file:
                return file.read()
        except IOError as error:
            if error.errno == errno.ENOENT:
                return json.dumps(None).encode()  # Redis requires data to be string or bytes.

    def _load(self):
        """Load the data from buffer or JSON file."""
        if _in_buffered_mode() or self._buffered:
            if self._filename in self._cache:
                # Load from buffer
                blob = self._cache[self._filename]
            else:
                # Load from file and store in buffer
                blob = self._load_from_file()
                self._store_to_buffer(self._filename, blob, store_hash=True)
        else:
            # Load from file
            blob = self._load_from_file()
        return json.loads(blob)

    @staticmethod
    def _write_to_file(filename, blob, write_concern=True):
        """Write the data to JSON file."""
        # When write_concern flag is set, we write the data into dummy file and
        # then replace that file with original file.
        if write_concern:
            dirname, fn = os.path.split(filename)
            fn_tmp = os.path.join(dirname, f'._{uuid.uuid4()}_{fn}')
            with open(fn_tmp, 'wb') as tmpfile:
                tmpfile.write(blob)
            os.replace(fn_tmp, filename)
        else:
            with open(filename, 'wb') as file:
                file.write(blob)

    def _sync(self):
        """Write the data to file or buffer."""
        data = self.to_base()
        # Converting non-string keys to string
        data = _convert_key_to_str(data)
        # Serialize data
        blob = json.dumps(data).encode()

        if _in_buffered_mode() or self._buffered > 0:
            # write in buffer
            self._store_to_buffer(self._filename, blob)
        else:
            # write to file
            self._write_to_file(self._filename, blob, self._write_concern)


JSONCollection.add_validator(json_format_validator)
_register_buffered_backend(JSONCollection)


class JSONDict(JSONCollection, SyncedAttrDict):
    """A dict-like mapping interface to a persistent JSON file.

    The JSONDict inherits from :class:`~core.synced_collection.SyncedCollection`
    and :class:`~core.syncedattrdict.SyncedAttrDict`.

    .. code-block:: python

        doc = JSONDict('data.json', write_concern=True)
        doc['foo'] = "bar"
        assert doc.foo == doc['foo'] == "bar"
        assert 'foo' in doc
        del doc['foo']

    .. code-block:: python

        >>> doc['foo'] = dict(bar=True)
        >>> doc
        {'foo': {'bar': True}}
        >>> doc.foo.bar = False
        {'foo': {'bar': False}}

    .. warning::

        While the JSONDict object behaves like a dictionary, there are
        important distinctions to remember. In particular, because operations
        are reflected as changes to an underlying file, copying (even deep
        copying) a JSONDict instance may exhibit unexpected behavior. If a
        true copy is required, you should use the `to_base()` method to get a
        dictionary representation, and if necessary construct a new JSONDict
        instance: `new_dict = JSONDict(old_dict.to_base())`.

    Parameters
    ----------
    filename: str, optional
        The filename of the associated JSON file on disk (Default value = None).
    write_concern: bool, optional
        Ensure file consistency by writing changes back to a temporary file
        first, before replacing the original file (Default value = None).
    data: mapping, optional
        The intial data pass to JSONDict. Defaults to `list()`
    parent: object, optional
        A parent instance of JSONDict or None (Default value = None).
    """


class JSONList(JSONCollection, SyncedList):
    """A non-string sequence interface to a persistent JSON file.

    The JSONList inherits from :class:`~core.synced_collection.SyncedCollection`
    and :class:`~core.syncedlist.SyncedList`.

    .. code-block:: python

        synced_list = JSONList('data.json', write_concern=True)
        synced_list.append("bar")
        assert synced_list[0] == "bar"
        assert len(synced_list) == 1
        del synced_list[0]

    .. warning::

        While the JSONList object behaves like a list, there are
        important distinctions to remember. In particular, because operations
        are reflected as changes to an underlying file, copying (even deep
        copying) a JSONList instance may exhibit unexpected behavior. If a
        true copy is required, you should use the `to_base()` method to get a
        dictionary representation, and if necessary construct a new JSONList
        instance: `new_list = JSONList(old_list.to_base())`.

    Parameters
    ----------
    filename: str, optional
        The filename of the associated JSON file on disk (Default value = None).
    write_concern: bool, optional
        Ensure file consistency by writing changes back to a temporary file
        first, before replacing the original file (Default value = None).
    data: non-str Sequence, optional
        The intial data pass to JSONList
    parent: object, optional
        A parent instance of JSONList or None (Default value = None).
    """


SyncedCollection.register(JSONDict, JSONList)
