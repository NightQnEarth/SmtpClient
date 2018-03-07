import entering_data
import sending_message
import exceptions
import sys


if __name__ == '__main__':
    try:
        if sys.version_info < (3, 6):
            raise exceptions.VersionError
        sending_message.mail_sending(entering_data.input_data())
    except (exceptions.InputDataExceptions, exceptions.ServerException,
            exceptions.VersionError) as exception:
        print(exception)
        sys.exit(exception.return_exit_code())
