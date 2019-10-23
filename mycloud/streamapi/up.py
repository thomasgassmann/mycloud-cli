import time
from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.mycloudapi.requests.drive import PutObjectRequest
from mycloud.streamapi import UpStream, StreamDirection
from mycloud.streamapi.progress_report import ProgressReport, ProgressReporter
from mycloud.streamapi.stream_accessor import CloudStreamAccessor
from mycloud.constants import ENCRYPTION_CHUNK_LENGTH, MY_CLOUD_BIG_FILE_CHUNK_SIZE
from mycloud.common import operation_timeout


class UpStreamExecutor:

    def __init__(self, request_executor: MyCloudRequestExecutor, progress_reporter: ProgressReporter = None):
        self.request_executor = request_executor
        self.progress_reporter = progress_reporter
        self._tmp_total_read = 0
        self._tmp_bps = 0
        self._tmp_iteration = 0
        self._tmp_start_time = None
        self._tmp_current_object_resource = 0

    async def upload_stream(self, stream_accessor: CloudStreamAccessor):
        self._tmp_total_read = 0
        self._tmp_bps = 0
        self._tmp_iteration = 0
        self._tmp_start_time = time.time()

        file_stream = stream_accessor.get_stream()
        if file_stream.stream_direction != StreamDirection.Up:
            raise ValueError('Invalid stream direction')

        current_part_index = file_stream.continued_append_starting_index or 0
        if current_part_index < 0:
            raise ValueError('Part index cannot be negative')
        while not file_stream.is_finished():
            for transform in stream_accessor.get_transforms():
                transform.reset_state()
            generator = self._get_generator(
                file_stream, MY_CLOUD_BIG_FILE_CHUNK_SIZE, applied_transforms=stream_accessor.get_transforms())
            upload_to = stream_accessor.get_part_file(current_part_index)
            self._tmp_current_object_resource = upload_to
            part_put_request = PutObjectRequest(upload_to, generator)
            _ = await self.request_executor.execute_request(part_put_request)
            current_part_index += 1

        file_stream.close()

    def _get_generator(self, stream: UpStream, max_length=None, applied_transforms=None):
        total_read = 0
        break_execution = False
        stream_finished = False

        while True:
            read_bytes = None
            if break_execution:
                read_bytes = bytes([])
            else:
                read_bytes = UpStreamExecutor._safe_file_stream_read(
                    stream, ENCRYPTION_CHUNK_LENGTH)

            if (len(read_bytes) < ENCRYPTION_CHUNK_LENGTH or read_bytes == b'' or read_bytes is None) and not break_execution:
                stream_finished = True

            if applied_transforms is not None:
                for transform in applied_transforms:
                    read_bytes = transform.up_transform(
                        read_bytes, last=stream_finished or break_execution)

            yield read_bytes

            if stream_finished:
                stream.finished()
                break

            if break_execution:
                break

            total_read += len(read_bytes)
            if total_read > max_length if max_length is not None else False:
                break_execution = True

            self._tmp_total_read += len(read_bytes)
            self._tmp_iteration += 1
            self._tmp_bps = self._tmp_total_read / \
                (time.time() - self._tmp_start_time)

            if self.progress_reporter is not None:
                self.progress_reporter.report_progress(ProgressReport(
                    self._tmp_current_object_resource, self._tmp_bps, self._tmp_iteration, self._tmp_total_read))

    @staticmethod
    def _safe_file_stream_read(file_stream, length=None):
        def read_safe(values):
            if values['len'] is None:
                return values['stream'].read()
            return values['stream'].read(values['len'])
        return operation_timeout(read_safe, stream=file_stream, len=length)
