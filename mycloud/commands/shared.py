from mycloud.filesync.progress import ProgressTracker
from mycloud.mycloudapi import MyCloudRequestExecutor


def get_progress_tracker(skip_paths):
    tracker = ProgressTracker()
    if skip_paths is not None:
        tracker.set_skipped_paths(skip_paths)
    return tracker


def container(ctx):
    return ctx.obj['injector']


def executor_from_ctx(ctx):
    return ctx.obj['injector'].provide(MyCloudRequestExecutor)
