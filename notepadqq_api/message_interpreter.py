from notepadqq_api.notepadqq_message_error import NotepadqqMessageError
from notepadqq_api.stubs import Stubs

class MessageInterpreter():
    """Provides methods to invoke Notepadqq methods and to handle events."""

    def __init__(self, message_channel):
        """Construct a new MessageInterpreter object on the given
           MessageChannel.
        """
        self._message_channel = message_channel

        # Hash of event handlers, for example
        # {
        #   1: {
        #     "newWindow": [<callback1>, ..., <callbackn>]
        #   },
        #   ...
        # }
        # Where 1 is an object_id and "newWindow" is an event of that object
        self._event_handlers = {}

    def register_event_handler(self, object_id, event, callback):
        """Register an event handler."""
        obj_events = self._event_handlers.setdefault(object_id, {})
        evt_handlers = obj_events.setdefault(event, [])

        evt_handlers.append(callback)

    def invoke_api(self, object_id, method, args):
        """Call a remote Notepadqq method and get the result."""
        message = {
            'objectId': object_id,
            'method': method,
            'args': args
        }

        self._message_channel.send_message(message)
        reply = self._message_channel.get_next_result_message()

        result = [reply["result"]]
        self._convert_stubs(result)
        result = result[0]

        if reply["err"] != NotepadqqMessageError.ErrorCode.NONE:
            error = NotepadqqMessageError(reply["err"], reply["errStr"])
            raise error

        return result

    def process_message(self, message):
        """Process a message from Notepadqq"""
        if "event" in message:
            self._process_event_message(message)
        elif "result" in message:
            # We shouldn't have received it here... ignore it
            pass

    def _process_event_message(self, message):
        # Call the handlers associated with this event message

        event = message["event"]
        object_id = message["objectId"]

        if object_id in self._event_handlers and event in self._event_handlers[object_id]:
            handlers = self._event_handlers[object_id][event]

            args = message["args"]
            self._convert_stubs(args)

            for handler in reversed(handlers):
                handler(*args)

    def _convert_stubs(self, data_array):
        # Transform stub placeholders within data_array to the relative
        # instances of Stubs classes.

        # FIXME Use a stack

        for i, value in enumerate(data_array):
            if value is not None:
                if isinstance(value, list):
                    self._convert_stubs(value)

                elif isinstance(value, dict) and \
                     '$__nqq__stub_type' in value and \
                     'id' in value and \
                     isinstance(value['$__nqq__stub_type'], str) and \
                     isinstance(value['id'], int):

                    stub_type = value['$__nqq__stub_type']

                    try:
                        stub = getattr(Stubs, stub_type)
                        data_array[i] = stub(self, value['id'])
                    except:
                        print("Unknown stub: " + str(stub_type))

                elif isinstance(value, dict):
                    for key in value:
                        tmp_array = [value[key]]
                        self._convert_stubs(tmp_array)
                        value[key] = tmp_array[0]
