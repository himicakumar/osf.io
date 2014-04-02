# -*- coding: utf-8 -*-
import logging
import httplib as http
import os

from modularodm import Q

from website.project.model import NodeLog
from website.project.utils import serialize_node
from website.project.decorators import must_have_permission
from website.project.decorators import must_not_be_registration
from website.project.decorators import must_have_addon
from website.project.decorators import must_be_contributor_or_public
from website.addons.base.views import check_file_guid

from framework import request, redirect
from framework.exceptions import HTTPError

from website.addons.dropbox.model import DropboxFile
from website.addons.dropbox.client import get_node_addon_client
from website.addons.dropbox.utils import (
    render_dropbox_file, get_file_name, metadata_to_hgrid, clean_path,
    DropboxNodeLogger, make_file_response
)

logger = logging.getLogger(__name__)
debug = logger.debug


@must_have_permission('write')
@must_not_be_registration
@must_have_addon('dropbox', 'node')
def dropbox_delete_file(path, auth, node_addon, **kwargs):
    node = node_addon.owner
    if path and auth:
        client = get_node_addon_client(node_addon)
        client.file_delete(path)
        # log the event
        nodelogger = DropboxNodeLogger(node=node, auth=auth, path=path)
        nodelogger.log(NodeLog.FILE_REMOVED, save=True)
        return None
    raise HTTPError(http.BAD_REQUEST)


@must_have_permission('write')
@must_not_be_registration
@must_have_addon('dropbox', 'node')
def dropbox_upload(node_addon, auth, **kwargs):
    """View for uploading a file from the filebrowser interface. Must return
    the Rubeus/HGrid representation of the newly added file.
    """
    node = node_addon.owner
    # Route may or may not have a path
    path = kwargs.get('path', node_addon.folder)
    client = get_node_addon_client(node_addon)
    file_obj = request.files.get('file', None)
    node = node_addon.owner
    if path and file_obj and client:
        filepath = os.path.join(path, file_obj.filename)
        metadata = client.put_file(filepath, file_obj)
        permissions = {
            'edit': node.can_edit(auth),
            'view': node.can_view(auth)
        }
        # Log the event
        nodelogger = DropboxNodeLogger(node=node, auth=auth, path=filepath)
        nodelogger.log(NodeLog.FILE_ADDED, save=True)
        # Return the HGrid-formatted JSON response
        return metadata_to_hgrid(metadata,
            node=node, permissions=permissions), http.CREATED
    raise HTTPError(http.BAD_REQUEST)


@must_be_contributor_or_public
@must_have_addon('dropbox', 'node')
def dropbox_download(path, node_addon, **kwargs):
    if not path:
        raise HTTPError(http.BAD_REQUEST)
    client = get_node_addon_client(node_addon)
    revision = request.args.get('rev')
    fileobject, metadata = client.get_file_and_metadata(path, rev=revision)
    return make_file_response(fileobject, metadata)


@must_be_contributor_or_public
@must_have_addon('dropbox', 'node')
def dropbox_get_revisions(path, node_addon, auth, **kwargs):
    """API view that gets a list of revisions for a file."""
    node = node_addon.owner
    client = get_node_addon_client(node_addon)
    # Get metadata for each revision of the file
    # Don't show deleted revisions
    revisions = [rev for rev in client.revisions(path) if not rev.get('is_deleted')]
    file_obj = DropboxFile.find_one(Q('node', 'eq', node) & Q('path', 'eq', path))
    # Add download links
    for revision in revisions:
        revision['download'] = file_obj.download_url(guid=True, rev=revision['rev'])
        revision['view'] = node.web_url_for('dropbox_view_file',
            path=path, rev=revision['rev'])
    return {
        'result': revisions,
        'registered': node.registered_date.isoformat() if node.registered_date else None,
    }, http.OK


@must_be_contributor_or_public
@must_have_addon('dropbox', 'node')
def dropbox_view_file(path, node_addon, auth, **kwargs):
    """Web view for the file detail page."""
    if not path:
        raise HTTPError(http.NOT_FOUND)
    node = node_addon.owner
    client = get_node_addon_client(node_addon)
    # Lazily create a file GUID record
    file_obj, created = DropboxFile.get_or_create(node=node, path=path)

    redirect_url = check_file_guid(file_obj)
    if redirect_url:
        return redirect(redirect_url)
    rev = request.args.get('rev')
    rendered = render_dropbox_file(file_obj, client=client, rev=rev)
    cleaned_path = clean_path(path)
    response = {
        'revisions_url': node.api_url_for('dropbox_get_revisions',
            path=cleaned_path, rev=rev),  # Append current revision as a query param
        'file_name': get_file_name(path),
        'render_url': node.api_url_for('dropbox_render_file', path=cleaned_path),
        'download_url': file_obj.download_url(guid=True, rev=rev),
        'rendered': rendered,
    }
    response.update(serialize_node(node, auth, primary=True))
    return response, http.OK

##### MFR Rendering #####

@must_be_contributor_or_public
@must_have_addon('dropbox', 'node')
def dropbox_render_file(path, node_addon, auth, **kwargs):
    """View polled by the FileRenderer. Return the rendered HTML for the
    requested file.
    """
    node = node_addon.owner
    file_obj = DropboxFile.find_one(Q('node', 'eq', node) & Q('path', 'eq', path))
    client = get_node_addon_client(node_addon)
    rev = request.args.get('rev')
    return render_dropbox_file(file_obj, client=client, rev=rev)