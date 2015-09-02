import threading, queue, datetime
from django.conf import settings

class timeouted_call :
    # class variable, shared by all timeouted_call
    semaphore = threading.BoundedSemaphore (settings.MAX_THREADS_NUMBER);

    def __init__ (self, func,timeout) :
        self.func = func
        self.timeout = timeout

    def run (self, args = None) :

        _t0 = datetime.datetime.now ()
        result_queue = queue.Queue ()

        # do not exceed max thread number
        def locked_func () :
            if not self.semaphore.acquire (True, int (self.timeout - (datetime.datetime.now () - _t0).total_seconds ())) :
                return { 'ok' : False,
                         'message' : "Max threads already working"}
            try :
                result_queue.put (self.func () if args == None else self.func (args))
            except :
                self.semaphore.release ()
                raise;
            self.semaphore.release ()

        action_thread = threading.Thread (None, locked_func)
        action_thread.start ()
        action_thread.join (self.timeout - (datetime.datetime.now () - _t0).total_seconds ())

        # When call has timeouted (be aware, worker is still working, but no one would care)
        if action_thread.is_alive () :
            return { 'ok' : False,
                     'message' : "Call took to much time"}

        # else get message from woker thread
        return { 'ok' : True, 'result' : result_queue.get () }

