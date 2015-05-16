class Stubs:
    class Stub:

        def __init__(self, message_interpreter, object_id):
            self._message_interpreter = message_interpreter
            self._object_id = object_id

        def on(self, event, callback):
            self._message_interpreter.register_event_handler(self._object_id, event, callback)

        def __getattr__(self, name):
            def _missing(*args, **kwargs):
                return self._message_interpreter.invoke_api(self._object_id, name, args)
            return _missing

        def __eq__(self, other):
            return isinstance(other, Stubs.Stub) and self._object_id == other._object_id and self._message_interpreter == other._message_interpreter

    class Notepadqq(Stub): pass
    class Editor(Stub): pass
    class Window(Stub): pass
    class MenuItem(Stub): pass