# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
"""Contrib submodule containing Project class and indexing features."""

import logging

<<<<<<< HEAD
from .collection import Collection
=======
>>>>>>> 977c9e3bb7a68bd9588416d680c4c18d89b1c286
from .project import Project, TemporaryProject, get_job, get_project, init_project

logger = logging.getLogger(__name__)


__all__ = [
    "Project",
    "TemporaryProject",
    "get_project",
    "init_project",
    "get_job",
<<<<<<< HEAD
    "Collection",
=======
>>>>>>> 977c9e3bb7a68bd9588416d680c4c18d89b1c286
]
