from logger import log


class ProgressReport:
    def __init__(self, object_resource: str, bps: int, iteration: int, uploaded_bytes: int):
        self.object_resource = object_resource
        self.bps = bps
        self.iteration = iteration
        self.uploaded_bytes = uploaded_bytes


class ProgressReporter:

    def report_progress(self, report: ProgressReport):
        if report.iteration % 1000 == 0:
            log(f'{report.object_resource}: {report.bps} bps | {report.iteration} iteration | {report.uploaded_bytes} bytes')
