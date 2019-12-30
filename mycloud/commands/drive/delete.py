import logging

import click
import inject

from mycloud.commands.shared import async_click, authenticated
from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.drive import DriveClient, DriveFailedToDeleteException
from mycloud.mycloudapi.requests.drive import (DeleteObjectRequest,
                                               MetadataRequest)


@click.command(name='delete')
@click.argument('remote')
@authenticated
@inject.params(client=DriveClient)
@async_click
async def delete_command(remote: str, client: DriveClient):
    try:
        await client.delete(remote)
    except DriveFailedToDeleteException:
        raise click.ClickException(f'Failed to delete {remote}')


async def _folder_deletion(executor: MyCloudRequestExecutor, remote: str):
    success = await _try_delete(executor, remote)
    logging.info(f'Trying to delete {remote}...')
    if not success:
        logging.info(f'Failed to delete {remote}!')
        metadata = MetadataRequest(remote)
        try:
            response = await executor.execute_request(metadata)
        except:
            logging.warning(f'{remote} does not exist')
            return
        (directories, files) = MetadataRequest.format_response(response)
        for remote_file in files:
            await _try_delete(executor, remote_file['Path'])
        for directory in directories:
            await _folder_deletion(executor, directory['Path'])


async def _try_delete(executor: MyCloudRequestExecutor, path: str):
    try:
        logging.info(f'Deleting {path}...')
        deletion_request = DeleteObjectRequest(path)
        response = await executor.execute_request(deletion_request)
        return response.status_code == 204
    except:
        return False
