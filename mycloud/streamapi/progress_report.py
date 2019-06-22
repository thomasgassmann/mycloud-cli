import logging


class ProgressReport:
    def __init__(self, object_resource: str, bps: int, iteration: int, uploaded_bytes: int):
        self.object_resource = object_resource
        self.bps = bps
        self.iteration = iteration
        self.uploaded_bytes = uploaded_bytes


class ProgressReporter:

    @staticmethod
    def report_progress(report: ProgressReport):
        if report.iteration % 1000 == 0:
            logging.info('{}: {} bps | {} iteration | {} bytes'.format(
                report.object_resource, report.bps, report.iteration, report.uploaded_bytes))
