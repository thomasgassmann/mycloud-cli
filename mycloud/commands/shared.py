import asyncio
import inject
import logging
from click import ClickException
from functools import update_wrapper
from mycloud.filesync.progress import ProgressTracker
from mycloud.mycloudapi import MyCloudRequestExecutor
from mycloud.mycloudapi.auth import MyCloudAuthenticator, AuthMode


def get_progress_tracker(skip_paths):
    tracker = ProgressTracker()
    if skip_paths is not None:
        tracker.set_skipped_paths(skip_paths)
    return tracker


def authenticated(func):
    def wrapper(*args, **kwargs):
        @inject.params(mycloud_authenticator=MyCloudAuthenticator)
        def inject_wrap(mycloud_authenticator: MyCloudAuthenticator):
            logging.debug(
                'Checking whether user can be authenticated for given command.')
            if mycloud_authenticator.auth_mode == None:
                raise ClickException(
                    'Run "mycloud auth login" to authenticate yourself first, or specify a token')
            else:
                func(*args, **kwargs)
        inject_wrap()

    return update_wrapper(wrapper, func)


def async_click(func):
    func = asyncio.coroutine(func)

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        logging.debug('Running asynchronous click action...')
        return loop.run_until_complete(func(*args, **kwargs))
    return update_wrapper(wrapper, func)
