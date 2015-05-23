import asyncio
import sys

from notepadqq_api.message_channel import MessageChannel
from notepadqq_api.message_interpreter import MessageInterpreter
from notepadqq_api.stubs import Stubs

class NotepadqqApi():
    """Provides access to the Notepadqq Api."""

    _NQQ_STUB_ID = 1

    def __init__(self, socket_path=None, extension_id=None):
        """Construct a new Api object that can be used to invoke Notepadqq
           methods and to receive its events.
           If not provided, socket_path and extension_id are respectively
           sys.argv[1] and sys.argv[2]
        """
        if socket_path is None:
            try:
                socket_path = sys.argv[1]
            except IndexError:
                raise ValueError("Socket path not provided")    
                
        if extension_id is None:
            try:
                extension_id = sys.argv[2]
            except IndexError:
                raise ValueError("Extension id not provided")
            
        self._socket_path = socket_path
        self._extension_id = extension_id

        self._message_channel = MessageChannel(self._socket_path)
        self._message_interpreter = MessageInterpreter(self._message_channel)

        self._nqq = Stubs.Notepadqq(self._message_interpreter, self._NQQ_STUB_ID)

    def run_event_loop(self, started_callback=None):
        """Start the event loop. If started_callback is provided, it will
           be called as soon as the connection with Notepadqq is ready.
        """
        if started_callback is not None:
            self.notepadqq.on('currentExtensionStarted', started_callback)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._message_channel.start(loop, self._on_new_message))

    @property
    def extension_id(self):
        """The id assigned to this extension by Notepadqq"""
        return self._extension_id

    @property
    def notepadqq(self):
        """Get an instance of the main Notepadqq object"""
        return self._nqq

    def on_window_created(self, callback):
        """Execute a callback for every new window.
           This is preferable to the "newWindow" event of Notepadqq, because it
           could happen that the extension isn't ready soon enough to receive
           the "newWindow" event for the first window. This method, instead,
           ensures that the passed callback will be called once and only once
           for each current or future window.
        """
        captured_windows = []

        # Invoke the callback for every currently open window
        for window in self.notepadqq.windows():
            if window not in captured_windows:
                captured_windows.append(window)
                callback(window)

        # Each time a new window gets opened, invoke the callback.
        # When Notepadqq is starting and initializing all the extensions,
        # we might not be fast enough to receive this event: this is why
        # we manually invoked the callback for every currently open window.
        def on_new_window(window):
            if window not in captured_windows:
                callback(window)

        self.notepadqq.on('newWindow', on_new_window)

    def _on_new_message(self, msg):
        # Called whenever a new message is received from the channel
        self._message_interpreter.process_message(msg)
