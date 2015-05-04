#!/usr/bin/env python
# encoding: utf-8

from . import routes, views, model, oldels

MODELS = [
    model.OsfStorageFileNode,
    model.OsfStorageGuidFile,
<<<<<<< HEAD
    # model.OsfStorageFileNode
=======
    model.OsfStorageFileVersion,
    model.OsfStorageNodeSettings,
    oldels.OsfStorageFileTree,
    oldels.OsfStorageFileRecord,
>>>>>>> cbfbd12bf81ef4ed3ed2fe9650a57506b32b9a4e
]
NODE_SETTINGS_MODEL = model.OsfStorageNodeSettings

ROUTES = [
    routes.api_routes
]

SHORT_NAME = 'osfstorage'
FULL_NAME = 'OSF Storage'

OWNERS = ['node']

ADDED_DEFAULT = ['node']
ADDED_MANDATORY = ['node']

VIEWS = []
CONFIGS = []

CATEGORIES = ['storage']

INCLUDE_JS = {
    'widget': [],
    'page': [],
    'files': [],
}

HAS_HGRID_FILES = True
GET_HGRID_DATA = views.osf_storage_root

MAX_FILE_SIZE = 128  # 128 MB
HIGH_MAX_FILE_SIZE = 5 * 1024  # 5 GB

# HERE = os.path.dirname(os.path.abspath(__file__))
NODE_SETTINGS_TEMPLATE = None  # no node settings view
USER_SETTINGS_TEMPLATE = None  # no user settings view
