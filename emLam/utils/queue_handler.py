#!/usr/bin/env python
"""
QueueHandler and QueueListener Python 2.7. See
- http://plumberjack.blogspot.hu/2010/09/using-logging-with-multiprocessing.html
- http://gist.github.com/591589 (improved version from the link above)
- http://plumberjack.blogspot.hu/2010/09/improved-queuehandler-queuelistener.html
"""

# Copyright (C) 2010 Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Vinay Sajip
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
# Above copyright only concerns the implementation of the two classes; the
# scaffolding code is mine and is under the same license as the rest of emLam.

from __future__ import absolute_import
import logging
import queue
import platform
import threading

if float(platform.python_version().rsplit('.', 1)[0]) >= 3.2:
    from logging.handlers import QueueHandler, QueueListener
else:
    class QueueHandler(logging.Handler):
        """
        This handler sends events to a queue. Typically, it would be used together
        with a multiprocessing Queue to centralise logging to file in one process
        (in a multi-process application), so as to avoid file write contention
        between processes.
        This code is new in Python 3.2, but this class can be copy pasted into
        user code for use with earlier Python versions.
        """

        def __init__(self, queue):
            """
            Initialise an instance, using the passed queue.
            """
            logging.Handler.__init__(self)
            self.queue = queue

        def enqueue(self, record):
            """
            Enqueue a record.
            The base implementation uses put_nowait. You may want to override
            this method if you want to use blocking, timeouts or custom queue
            implementations.
            """
            self.queue.put_nowait(record)

        def prepare(self, record):
            """
            Prepares a record for queueing. The object returned by this
            method is enqueued.

            The base implementation formats the record to merge the message
            and arguments, and removes unpickleable items from the record
            in-place.

            You might want to override this method if you want to convert
            the record to a dict or JSON string, or send a modified copy
            of the record while leaving the original intact.
            """
            # The format operation gets traceback text into record.exc_text
            # (if there's exception data), and also puts the message into
            # record.message. We can then use this to replace the original
            # msg + args, as these might be unpickleable. We also zap the
            # exc_info attribute, as it's no longer needed and, if not None,
            # will typically not be pickleable.
            self.format(record)
            record.msg = record.message
            record.args = None
            record.exc_info = None
            return record

        def emit(self, record):
            """
            Emit a record.
            Writes the LogRecord to the queue, preparing it first.
            """
            try:
                self.enqueue(self.prepare(record))
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                self.handleError(record)


    class QueueListener(object):

        _sentinel = None

        def __init__(self, queue, handler):
            """
            Initialise an instance with the specified queue and
            handler.
            """
            self.queue = queue
            self.handler = handler
            self._stop = threading.Event()
            self._thread = None

        def dequeue(self, block):
            """
            Dequeue a record and return it, optionally blocking.

            The base implementation uses get. You may want to override this method
            if you want to use timeouts or work with custom queue implementations.
            """
            return self.queue.get(block)

        def start(self):
            """
            Start the listener.

            This starts up a background thread to monitor the queue for
            LogRecords to process.
            """
            self._thread = t = threading.Thread(target=self._monitor)
            t.setDaemon(True)
            t.start()

        def _monitor(self):
            """
            Monitor the queue for records, and ask the handler
            to deal with them.

            This method runs on a separate, internal thread.
            The thread will terminate if it sees a sentinel object in the queue.
            """
            q = self.queue
            has_task_done = hasattr(q, 'task_done')
            while not self._stop.isSet():
                try:
                    record = self.dequeue(True)
                    if record is self._sentinel:
                        break
                    self.handler.handle(record)
                    if has_task_done:
                        q.task_done()
                except queue.Empty:
                    pass
            # There might still be records in the queue.
            while True:
                try:
                    record = self.dequeue(False)
                    if record is self._sentinel:
                        break
                    self.handler.handle(record)
                    if has_task_done:
                        q.task_done()
                except queue.Empty:
                    break

        def stop(self):
            """
            Stop the listener.

            This asks the thread to terminate, and then waits for it to do so.
            """
            self._stop.set()
            self.queue.put_nowait(self._sentinel)
            self._thread.join()
            self._thread = None
