from mycloud.common import MyCloudException


class DriveNotFoundException(MyCloudException):
    pass


class DriveFailedToDeleteException(MyCloudException):
    pass
