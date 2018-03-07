class ServerException(Exception):
    def __init__(self, server_response):
        self.server_response = server_response

    def __str__(self):
        return "\n\rServer error:\n\r***\n\r{}\n\r***".format(
            self.server_response)

    def return_exit_code(self):
        return int(self.server_response[0:3])


def exit_code(code):
    def return_exit_code(self):
        return code

    def exit_code_decorator(exception):
        exception.return_exit_code = return_exit_code
        return exception
    return exit_code_decorator


class InputDataExceptions(Exception):
    pass


@exit_code(1)
class NotEnteredRecipientsError(InputDataExceptions):
    def __str__(self):
        return "You have entered none recipients addresses."


@exit_code(2)
class IncorrectRecipientAddressError(InputDataExceptions):
    def __init__(self, address_number, from_file=False):
        self.address_number = address_number
        self.from_file = from_file

    def __str__(self):
        line_or_number = 'address number'
        if self.from_file:
            line_or_number = 'line'

        return "Incorrect recipient's address, {} {}.".format(
            line_or_number, self.address_number)


@exit_code(3)
class IncorrectServerError(InputDataExceptions):
    def __str__(self):
        return "Entered incorrect server address."


@exit_code(4)
class IncorrectPortError(InputDataExceptions):
    def __str__(self):
        return "Entered incorrect port number."


@exit_code(5)
class IncorrectFileNameError(InputDataExceptions):
    def __init__(self, filename):
        self.filename = filename

    def __str__(self):
        return 'Not found file "{}".'.format(self.filename)


@exit_code(6)
class IncorrectAttachError(InputDataExceptions):
    def __str__(self):
        return "Entered incorrect attach."


@exit_code(7)
class FileError(InputDataExceptions):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


@exit_code(8)
class VersionError(Exception):
    def __str__(self):
        return "Python 3.6 or higher is required."
