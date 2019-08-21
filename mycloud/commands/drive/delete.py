import logging
import click
from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.mycloudapi.requests.drive import DeleteObjectRequest, MetadataRequest
from mycloud.commands.shared import executor_from_ctx, async_click, authenticated


@click.command(name='delete')
@click.pass_context
@click.argument('remote')
@async_click
@authenticated
async def delete_command(ctx, remote: str):
    executor = executor_from_ctx(ctx)
    await _folder_deletion(executor, remote)


async def _folder_deletion(executor: MyCloudRequestExecutor, remote: str):
    success = _try_delete(executor, remote)
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
            _folder_deletion(executor, directory['Path'])


async def _try_delete(executor: MyCloudRequestExecutor, path: str):
    try:
        logging.info(f'Deleting {path}...')
        deletion_request = DeleteObjectRequest(path)
        response = await executor.execute_request(deletion_request)
        return response.status_code == 204
    except:
        return False
