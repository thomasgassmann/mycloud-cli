import click
from typing import List
from mycloud.filesystem import FileManager
from mycloud.filesync import downsync_folder
from mycloud.mycloudapi import ObjectResourceBuilder, DeleteObjectRequest, MetadataRequest
from mycloud.filesystem import BasicRemotePath
from mycloud.commands.shared import get_progress_tracker, executor_from_ctx


@click.command(name='delete')
@click.pass_context
@click.argument('remote')
def delete_command(ctx, remote: str):
    executor = executor_from_ctx(ctx)
    _folder_deletion(executor, remote)


def _folder_deletion(executor, remote):
    success = _try_delete(executor, remote)
    print(f'Trying to delete {remote}...')
    if not success:
        print(f'Failed to delete {remote}!')
        metadata = MetadataRequest(remote)
        response = executor.execute_request(metadata)
        (directories, files) = MetadataRequest.format_response(response)
        for directory in directories:
            _folder_deletion(executor, directory['Path'])
        for remote_file in files:
            _try_delete(executor, remote_file['Path'])


def _try_delete(executor, path):
    try:
        deletion_request = DeleteObjectRequest(path)
        response = executor.execute_request(deletion_request)
        return response.status_code == 204
    except:
        return False
    