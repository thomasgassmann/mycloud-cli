import logging
import click
from typing import List
from mycloud.filesystem import FileManager
from mycloud.filesync import downsync_folder
from mycloud.mycloudapi import ObjectResourceBuilder, DeleteObjectRequest, MetadataRequest, MyCloudRequestExecutor
from mycloud.filesystem import BasicRemotePath
from mycloud.commands.shared import get_progress_tracker, executor_from_ctx


@click.command(name='delete')
@click.pass_context
@click.argument('remote')
def delete_command(ctx, remote: str):
    executor = executor_from_ctx(ctx)
    _folder_deletion(executor, remote)


def _folder_deletion(executor: MyCloudRequestExecutor, remote: str):
    success = _try_delete(executor, remote)
    logging.info(f'Trying to delete {remote}...')
    if not success:
        logging.info(f'Failed to delete {remote}!')
        metadata = MetadataRequest(remote)
        response = executor.execute_request(metadata)
        (directories, files) = MetadataRequest.format_response(response)
        for remote_file in files:
            _try_delete(executor, remote_file['Path'])
        for directory in directories:
            _folder_deletion(executor, directory['Path'])


def _try_delete(executor: MyCloudRequestExecutor, path: str):
    try:
        logging.info(f'Deleting {path}...')
        deletion_request = DeleteObjectRequest(path)
        response = executor.execute_request(deletion_request)
        return response.status_code == 204
    except:
        return False
