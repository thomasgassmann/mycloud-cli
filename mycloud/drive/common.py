from typing import AsyncIterator
from mycloud.drive.drive_client import DriveClient
from mycloud.mycloudapi.requests.drive import FileEntry


# methods / helpers, that are not relevant for the core DriveClient, but depend on it

async def ls_files_recursively(client: DriveClient, remote: str) -> AsyncIterator[FileEntry]:
    metadata = await client.ls(remote)
    for file in metadata.files:
        yield file
    for directory in metadata.dirs:
        async for item in ls_files_recursively(client, remote):
            yield item
