from mycloud.filesync.progress import ProgressTracker
from mycloud.mycloudapi import MyCloudRequestExecutor


def get_progress_tracker(skip_paths):
    tracker = ProgressTracker()
    if skip_paths is not None:
        skipped = ', '.join(skip_paths)
        tracker.set_skipped_paths(skip_paths)
    return tracker


def executor_from_ctx(ctx):
    return ctx.obj['injector'].provide(MyCloudRequestExecutor)
