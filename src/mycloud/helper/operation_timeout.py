from sys import platform
import signal, threading


class CouldNotReadFileException(Exception):
    def __str__(self):
        return 'Could not read the specified file within the time given'


def operation_timeout(operation, **kwargs):
    timeout = 15
    if platform == 'win32':
        return _operation_timeout_win32(operation, timeout, dict=kwargs)
    else:
        return _operation_timeout_sigalrm(operation, timeout, dict=kwargs)


def _operation_timeout_win32(operation, timeout, dict):
    class FuncThread(threading.Thread):

        def __init__(self):
            threading.Thread.__init__(self)
            self.result = None


        def run(self):
            self.result = operation(dict)

    it = FuncThread()
    it.start()
    it.join(timeout)
    if it.is_alive() or it.result is None:
        raise CouldNotReadFileException
    else:
        return it.result


def _operation_timeout_sigalrm(operation, timeout, dict):
    def handler(a, b):
        raise CouldNotReadFileException
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(timeout)
    ret = None
    try:
        ret = operation(dict)
    except CouldNotReadFileException:
        pass
        
    signal.alarm(0)
    if ret is None:
        raise CouldNotReadFileException
    return ret