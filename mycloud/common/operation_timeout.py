import threading
from mycloud.constants import MAX_TIMEOUT


class TimeoutException(Exception):
    def __str__(self):
        return 'Could not read the specified file within the time given'


def operation_timeout(operation, **kwargs):
    return _operation_timeout(operation, MAX_TIMEOUT, values=kwargs)


def _operation_timeout(operation, timeout, values):
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
    return func_thread.result
