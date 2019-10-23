import time
from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.mycloudapi.requests.drive import GetObjectRequest
from mycloud.streamapi import StreamDirection
from mycloud.streamapi.progress_report import ProgressReport, ProgressReporter
from mycloud.streamapi.stream_accessor import CloudStreamAccessor
from mycloud.constants import ENCRYPTION_CHUNK_LENGTH


class DownStreamExecutor:

    def __init__(self, request_executor: MyCloudRequestExecutor, progress_reporter: ProgressReporter = None):
        self.request_executor = request_executor
        self.progress_reporter = progress_reporter

    async def download_stream(self, stream_accessor: CloudStreamAccessor):
        tmp_total_read = 0
        tmp_iteration = 0
        tmp_start_time = time.time()

        file_stream = stream_accessor.get_stream()
        if file_stream.stream_direction != StreamDirection.Down:
            raise ValueError('Invalid stream direction')

        current_part_index = file_stream.continued_append_starting_index or 0
        while not file_stream.is_finished():
            for transform in stream_accessor.get_transforms():
                transform.reset_state()
            resource_url = stream_accessor.get_part_file(current_part_index)
            get_request = GetObjectRequest(resource_url, ignore_not_found=True)
            response = await self.request_executor.execute_request(get_request)
            if response.status_code == 404:
                file_stream.finished()
                break

            def _transform_chunk(current_chunk, is_last):
                nonlocal tmp_total_read
                nonlocal tmp_iteration
                nonlocal tmp_start_time
                for transform in stream_accessor.get_transforms():
                    current_chunk = transform.down_transform(
                        current_chunk, last=is_last)
                file_stream.write(current_chunk)

                tmp_total_read += len(current_chunk)
                tmp_bps = tmp_total_read / (time.time() - tmp_start_time)
                tmp_iteration += 10

                if self.progress_reporter is not None:
                    self.progress_reporter.report_progress(ProgressReport(
                        resource_url, tmp_bps, tmp_iteration, tmp_total_read))

            previous_chunk = None

            for chunk in response.iter_content(chunk_size=ENCRYPTION_CHUNK_LENGTH):
                if previous_chunk is None:
                    previous_chunk = chunk
                    continue

                _transform_chunk(previous_chunk, is_last=False)
                previous_chunk = chunk

            _transform_chunk(previous_chunk, is_last=True)
            current_part_index += 1

        file_stream.close()
