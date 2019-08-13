import asyncio
from functools import update_wrapper
from mycloud.filesync.progress import ProgressTracker
from mycloud.mycloudapi import MyCloudRequestExecutor


def get_progress_tracker(skip_paths):
    tracker = ProgressTracker()
    if skip_paths is not None:
        tracker.set_skipped_paths(skip_paths)
    return tracker


def container(ctx):
    return ctx.obj['injector']


def provide(ctx, t):
    return ctx.obj['injector'].provide(t)


def executor_from_ctx(ctx):
    return ctx.obj['injector'].provide(MyCloudRequestExecutor)


def async_click(func):
    func = asyncio.coroutine(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))
    return update_wrapper(wrapper, func)
