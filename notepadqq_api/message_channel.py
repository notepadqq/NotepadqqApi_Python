import logging
import socket
import json
import threading
import asyncio

class MessageChannel():
    """Send messages to Notepadqq and receive responses."""

    def __init__(self, socket_path):
        """Initialize a new channel on the specified address."""
        # FIXME Windows support
        self._logger = logging.getLogger('MessageChannel')
        self._socket_path = socket_path
        self._unprocessed_messages = []

        # Condition variable for self._unprocessed_messages
        self._readCondition = threading.Condition()

        # Used to wake up the main thread event loop whenever new messages
        # are available.
        self._notifyRead, self._notifyWrite = None, None

        # Socket for communication with Notepadqq
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.setblocking(True)

    def start(self, loop, handler_callback):
        """Connect to the socket and start reading data. The passed callback
           will be called for each new incoming message.
        """
        self._notifyRead, self._notifyWrite = socket.socketpair()
        self._socket.connect(self._socket_path)

        # Get a stream reader for the notification socket
        notifyReader, _ = yield from asyncio.open_connection(sock=self._notifyRead, loop=loop)

        # Start the thread that will receive messages from the socket.
        t = threading.Thread(target=self._fill_buffer)
        t.start()

        while True:
            # Asynchronously wait for new messages
            yield from notifyReader.read(4096)

            while True:
                with self._readCondition:
                    if len(self._unprocessed_messages) > 0:
                        # Get the first message
                        data = self._unprocessed_messages.pop(0)
                    else:
                        break # from the inner while

                # Call the handler
                handler_callback(json.loads(data.decode()))

    def send_message(self, msg):
        """Sends a JSON message to Notepadqq."""
        self._send_raw_message(json.dumps(msg) + "\n")

    def get_next_result_message(self):
        """Synchronously wait and return the next result message."""
        # FIXME Get next result message with the specified request id, and 
        # in the meantime keep handling the messages that are not the requested one.
        retval = None

        while retval is None:
            with self._readCondition:
                # Look in self._unprocessed_messages for our result message.
                # Just for safety, we cycle again on each message even if we
                # already checked it in the previous iteration. Nobody should
                # read from self._unprocessed_messages while we're running this
                # function, but you never know who may pop the data.
                for i in range(0, len(self._unprocessed_messages)):
                    received_message = json.loads(self._unprocessed_messages[i].decode())

                    if "result" in received_message:
                        del self._unprocessed_messages[i]
                        retval = received_message
                        break # from the for

                if retval is None:
                    # Synchronously wait for new messages
                    self._readCondition.wait()

        return retval

    def _send_raw_message(self, msg):
        # Send a raw string message to Notepadqq.
        data = msg.encode()
        self._socket.send(data)
        self._logger.debug(">> Sent " + str(data))

    def _fill_buffer(self):
        # This should run in a different thread. It reads messages from the
        # channel and puts them in self._unprocessed_messages.
        buf = b''

        while True:
            buf += self._socket.recv(4096)
            parts = buf.split(b'\n')

            # The last element is always partial.
            buf = parts.pop()

            # Print received data for debug
            if self._logger.getEffectiveLevel() == logging.DEBUG:
                for p in parts:
                    self._logger.debug("<< Received " + str(p))

            with self._readCondition:
                self._unprocessed_messages.extend(parts)
                # Notify whoever is blocked waiting for new messages
                # (e.g. self.get_next_result_message)
                self._readCondition.notify()

            # Notify event loop (e.g. unlock self.start)
            self._notifyWrite.send(b'.')
