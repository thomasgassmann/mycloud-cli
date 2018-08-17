from mycloud.logger import log


class ProgressReport:
    def __init__(self, object_resource: str, bps: int, iteration: int, uploaded_bytes: int):
        self.object_resource = object_resource
        self.bps = bps
        self.iteration = iteration
        self.uploaded_bytes = uploaded_bytes


class ProgressReporter:

    def report_progress(self, report: ProgressReport):
        if report.iteration % 1000 == 0:
            log('{}: {} bps | {} iteration | {} bytes'.format(report.object_resource, report.bps, report.iteration, report.uploaded_bytes))
