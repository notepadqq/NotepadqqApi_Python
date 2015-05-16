class NotepadqqMessageError(RuntimeError):
    """An error from Notepadqq"""

    class ErrorCode:
        NONE = 0
        INVALID_REQUEST = 1
        INVALID_ARGUMENT_NUMBER = 2
        INVALID_ARGUMENT_TYPE = 3
        OBJECT_DEALLOCATED = 4
        OBJECT_NOT_FOUND = 5
        METHOD_NOT_FOUND = 6

    def __init__(self, error_code, error_string):
        self._error_code = error_code
        self._error_string = error_string

        super(NotepadqqMessageError, self).__init__(self.description)

    @property
    def error_code(self):
        return self._error_code

    @property
    def error_string(self):
        return self._error_string

    @property
    def description(self):

        if self._error_code == self.ErrorCode.NONE: descr = "None"
        elif self._error_code == self.ErrorCode.INVALID_REQUEST: descr = "Invalid request"
        elif self._error_code == self.ErrorCode.INVALID_ARGUMENT_NUMBER: descr = "Invalid argument number"
        elif self._error_code == self.ErrorCode.INVALID_ARGUMENT_TYPE: descr = "Invalid argument type"
        elif self._error_code == self.ErrorCode.OBJECT_DEALLOCATED: descr = "Object deallocated"
        elif self._error_code == self.ErrorCode.OBJECT_NOT_FOUND: descr = "Object not found"
        elif self._error_code == self.ErrorCode.METHOD_NOT_FOUND: descr = "Method not found"
        else: descr = "Unknown error"

        if self._error_string is not None and self._error_string != "":
            descr += ': ' + self._error_string

        return descr