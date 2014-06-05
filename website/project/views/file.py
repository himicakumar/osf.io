"""
Files views.
"""
import os
import codecs
import logging
import httplib as http
from website.util import rubeus

from framework.flask import request, secure_filename
from framework.exceptions import HTTPError
from framework.render.tasks import build_rendered_html
from framework.auth.decorators import Auth

from website.project.decorators import must_be_contributor_or_public, must_have_valid_signature, must_be_valid_project
from website import settings
from website.project.views.node import _view_project


logger = logging.getLogger(__name__)
debug = logger.debug


@must_be_contributor_or_public
def collect_file_trees(**kwargs):
    """Collect file trees for all add-ons implementing HGrid views, then
    format data as appropriate.
    """
    node = kwargs['node'] or kwargs['project']
    auth = kwargs['auth']

    serialized = _view_project(node, auth)
    # Add addon static assets
    serialized.update(rubeus.collect_addon_assets(node))
    return serialized

@must_be_contributor_or_public
def grid_data(**kwargs):
    """View that returns the formatted data for rubeus.js/hgrid
    """
    node = kwargs['node'] or kwargs['project']
    auth = kwargs['auth']
    data = request.args.to_dict()
    return {'data': rubeus.to_hgrid(node, auth, **data)}

# File rendering
def get_cache_path(node_settings):
    return os.path.join(
        settings.MFR_CACHE_PATH,
        node_settings.config.short_name,
        node_settings.owner._id,
    )


def get_cache_content(node_settings, cache_file, start_render=False,
                      file_path=None, file_content=None, download_path=None):
    """

    """
    # Get rendered content if present
    cache_path = get_cache_path(node_settings)
    cache_file_path = os.path.join(cache_path, cache_file)
    try:
        return codecs.open(cache_file_path, 'r', 'utf-8').read()
    except IOError:
        # Start rendering job if requested
        if start_render:
            build_rendered_html(
                file_path, file_content, cache_path, cache_file_path,
                download_path
            )
        return None


def prepare_file(file):

    name = secure_filename(file.filename)
    content = file.read()
    content_type = file.content_type
    file.seek(0, os.SEEK_END)
    size = file.tell()

    return name, content, content_type, size

@must_be_valid_project
@must_have_valid_signature
def add_file_to_node(**kwargs):
    upload = request.files.get('file')
    if not upload:
        raise HTTPError(http.BAD_REQUEST)
    
    name, content, content_type, size = prepare_file(upload)
    
    node = kwargs.get('node')
    if not node:
        raise HTTPError(http.BAD_REQUEST)
    auth = Auth(user=node.contributors[0])

    node.add_file(
        auth=auth,
        file_name=name,
        content=content,
        size=size,
        content_type=content_type,
    )
    node.save()
    return {"status": "Upload success"}
