import inject
import os
from wsgidav.dav_provider import DAVNonCollection
from mycloud.webdav.client import MyCloudDavClient, FileEntry
from mycloud.common import to_unix


class FileResource(DAVNonCollection):

    dav_client: MyCloudDavClient = inject.attr(MyCloudDavClient)

    def __init__(self, path, environ):
        super().__init__(path, environ)

    def get_last_modified(self):
        return to_unix(self._file_entry.modification_time)

    def get_content_length(self):
        return self._file_entry.length

    def get_content_type(self):
        return self._file_entry.mime

    def get_display_name(self):
        return self._file_entry.name

    def support_etag(self):
        return True

    def get_etag(self):
        return self._file_entry.etag

    def support_ranges(self):
        return False

    def get_content(self):
        return self.dav_client.open_read(self.path)

    def begin_write(self, content_type):
        return self.dav_client.open_write(self.path)

    def end_write(self, with_errors):
        self.remove_all_locks(True)

    def copy_move_single(self, dest_path, is_move):
        if is_move:
            self.move_recursive(dest_path)
            return

    def support_recursive_move(self, path):
        return True

    def move_recursive(self, path):
        self.dav_client.move(self.path, path)

    def delete(self):
        self.dav_client.remove(self.path)
        self.remove_all_properties(True)
        self.remove_all_locks(True)

    @property
    def _file_entry(self):
        dir_name = os.path.dirname(os.path.normpath(self.path))
        metadata = self.dav_client.get_directory_metadata(dir_name)
        res = list(filter(lambda x: x.path == self.path, metadata.files))
        if any(res):
            return res[0]

        return FileEntry(
            creation_time=None,
            etag=None,
            extension=None,
            length=0,
            mime=None,
            modification_time=None,
            name=os.path.basename(os.path.normpath(self.path)),
            path=self.path)
