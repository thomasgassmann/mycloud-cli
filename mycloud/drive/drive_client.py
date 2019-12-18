import inject
from mycloud.mycloudapi import MyCloudRequestExecutor


class DriveClient:

    request_executor: MyCloudRequestExecutor = inject.attr(
        MyCloudRequestExecutor)
