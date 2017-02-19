# python2 requires: pip install futures
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from concurrent.futures._base import Future
from concurrent.futures.thread import _WorkItem
from functools import wraps
import time
import requests
from requests import Session


class Pool(ThreadPoolExecutor):

    '''timeout_return while .x called and timeout.'''

    def __init__(self, n=None, timeout=None, timeout_return=None):
        if n is None and (not isinstance(range,type)):
            # python2 n!=None
            n = 20
        super(Pool, self).__init__(n)
        self.timeout = timeout
        self.timeout_return = timeout_return

    def async_func(self, f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            return self.submit(f, *args, **kwargs)
        return wrapped

    def submit(self, func, *args, **kwargs):
        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError(
                    'cannot schedule new futures after shutdown')
            future = NewFuture(
                self.timeout, self.timeout_return, args, kwargs)
            w = _WorkItem(future, func, args, kwargs)
            self._work_queue.put(w)
            self._adjust_thread_count()
            return future


class NewFuture(Future):

    """add .x (property) and timeout/timeout_return args for original Future
    timeout_return function only can be called while .x attribute called and raise TimeoutError.
    WARNING: Future thread will not stop running until function finished or pid killed.
    """

    def __init__(self, timeout=None, timeout_return=None, args=(), kwargs={}):
        super(NewFuture, self).__init__()
        self._timeout = timeout
        self._timeout_return = timeout_return
        self._args = args
        self._kwargs = kwargs

    def __getattr__(self, name):
        result = self.result(self._timeout)
        return result.__getattribute__(name)

    @property
    def x(self):
        try:
            return self.result(self._timeout)
        except TimeoutError:
            if not self._timeout_return:
                return 'TimeoutError: %s, %s' % (self._args, self._kwargs)
            if hasattr(self._timeout_return, '__call__'):
                return self._timeout_return(*self._args, **self._kwargs)
            return self._timeout_return


def Async(f, n=None, timeout=None, timeout_return=None):
    '''Here "Async" is not a class object, upper "A" only be used to differ
        from keyword "async" since python3.5+.
        Args:
        f : Async the function object, f.
        n=None: (os.cpu_count() or 1) * 5, The maximum number of threads that 
            can be used to execute the given calls.
        timeout=None: Future.x will wait for `timeout` seconds for the function's 
            result,  or return timeout_return(*args, **kwargs). 
            WARN: Future thread will not stop running until function finished or pid killed.
        timeout_return=None: Call Future.x after timeout, if timeout_return is 
            not true, return 'TimeoutError: %s, %s' % (self._args, self._kwargs) if timeout_return has __call__ attr, return timeout_return(*args, **kwargs) otherwise, return timeout_return itself.

        Read more from model __doc__.

'''
    return Pool(n, timeout, timeout_return).async_func(f)


def threads(n=None, timeout=None, timeout_return=None):
    '''Args:
        f : Async the function object, f.
        n=None: (os.cpu_count() or 1) * 5, The maximum number of threads that can be used to execute the given calls.
        timeout=None: Future.x will wait for `timeout` seconds for the function's result,  or return timeout_return(*args, **kwargs). WARN: Future thread will not stop running until function finished or pid killed.
        timeout_return=None: Call Future.x after timeout, if timeout_return is not true, return 'TimeoutError: %s, %s' % (self._args, self._kwargs) if timeout_return has __call__ attr, return timeout_return(*args, **kwargs) otherwise, return timeout_return itself.

        Read more from model __doc__.
'''
    return Pool(n, timeout, timeout_return).async_func


def get_by_time(new_futures, timeout=None):
    '''Return a generator'''
    try:
        for i in as_completed(new_futures, timeout=timeout):
            yield i.x
    except Exception as e:
        yield e


class tPool():

    def __init__(self, n=None, session=None, timeout=None, timeout_return=None):
        self.pool = Pool(n, timeout, timeout_return)
        self.n = n
        self.session = session if session else requests.Session()

    def close(self, wait=True):
        self.session.close()
        self.pool.shutdown(wait=wait)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def request(self, url, mode, retry=0, retrylog=False, logging=False,
                delay=0, fail_return=False, **kwargs):
        for _ in range(retry+1):
            try:
                time.sleep(delay)
                resp = self.session.request(mode, url, **kwargs)
                if logging:
                    print('%s done, %s' % (url, kwargs))
                return resp
            except Exception as e:
                if retrylog:
                    print('Retry %s for the %s time, Exception: %s . kwargs= %s' %
                              (url, _+1, e, kwargs))
                continue
        return fail_return

    def get(self, url, **kwargs):
        '''retry=0, retrylog=False, logging=None, delay=0, fail_return=False
            retry: retry time for exception
            logging: set logging=True will show url and kwargs when successful.
            retrylog: show error while catching exception after retrying.
            delay: time.sleep(delay) before request
            fail_return: return after retry arg `retry` times but fail
                , it may be a function(url, **args) or other.

        '''
        print(1)
        return self.pool.submit(self.request, url, 'get', **kwargs)

    def post(self, url, **kwargs):
        '''retry=0, retrylog=False, logging=None, delay=0, fail_return=False
            retry: retry time for exception
            logging: set logging=True will show url and kwargs when successful.
            retrylog: show error while catching exception after retrying.
            delay: time.sleep(delay) before request
            fail_return: return after retry arg `retry` times but fail
                , it may be a function(url, **args) or other.

        '''
        return self.pool.submit(self.request, url, 'post', **kwargs)

    def delete(self, url, **kwargs):
        return self.pool.submit(self.request, url, 'delete', **kwargs)

    def put(self, url, **kwargs):
        return self.pool.submit(self.request, url, 'put', **kwargs)

    def head(self, url, **kwargs):
        return self.pool.submit(self.request, url, 'head', **kwargs)
