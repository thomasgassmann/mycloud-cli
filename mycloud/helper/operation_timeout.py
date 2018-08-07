from sys import platform
import signal
import threading


class TimeoutException(Exception):
    def __str__(self):
        return 'Could not read the specified file within the time given'


def operation_timeout(operation, **kwargs):
    timeout = 15
    if platform == 'win32':
        return _operation_timeout_win32(operation, timeout, values=kwargs)
    else:
        return _operation_timeout_sigalrm(operation, timeout, values=kwargs)


def _operation_timeout_win32(operation, timeout, values):
    class FuncThread(threading.Thread):

        def __init__(self):
            super().__init__()
            self.result = None

        def run(self):
            self.result = operation(values)

    func_thread = FuncThread()
    func_thread.start()
    func_thread.join(timeout)
    if func_thread.is_alive() or func_thread.result is None:
        raise TimeoutException
    else:
        return func_thread.result


def _operation_timeout_sigalrm(operation, timeout, values):
    def handler(first, second):
        raise TimeoutException
    # pylint: disable=locally-disabled, no-member
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    ret = None
    try:
        ret = operation(values)
    except TimeoutException:
        pass

    signal.alarm(0)
    if ret is None:
        raise TimeoutException
    return ret
