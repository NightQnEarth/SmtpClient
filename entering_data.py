import argparse
import getpass
import sys
import re
import exceptions
from pathlib import Path


class EnteredData:
    __DEFAULT_PORT = 465

    def __init__(self, namespace):
        self.server_name = None
        self.port_number = None
        self.host_port_parser(namespace.server_port)
        self.sender_mail = namespace.sender_email[0]
        self.sender_password = None
        self.recipients_list = self.recipients_addresses_parser(
            namespace.mail_to)
        self.mail_subject = self.extract_subject_message(namespace.mail_topic)
        self.message = None
        self.attachments_list = []
        self.new_attach_name = None

        if namespace.attach:
            self.attachments_list, self.new_attach_name = \
                self.attachment_parser(namespace.attach)
        elif namespace.attaches:
            self.attachments_list = namespace.attaches

        for attachment in self.attachments_list:
            if not Path(attachment).exists():
                raise exceptions.IncorrectFileNameError(attachment)

        self.zip = namespace.zip
        self.debug = namespace.debug
        self.open_sending = namespace.open_sending
        self.max_size = namespace.max_size
        self.zip_file_content = None

    def host_port_parser(self, host_port_string):
        host_port_list = host_port_string.split(':', 2)
        self.server_name = self.check_server(host_port_list[0])
        self.port_number = self.check_port(
            self.__DEFAULT_PORT if len(host_port_list) == 1
            else host_port_list[1])

    @staticmethod
    def check_server(server):
        server_regex = re.compile(r'([a-zA-Z0-9_.+-]+\.)+[a-zA-Z0-9_.+-]+')

        if server_regex.fullmatch(server):
            return server
        raise exceptions.IncorrectServerError

    @staticmethod
    def check_port(port):
        port_regex = re.compile(r'\d+')

        if port_regex.fullmatch(str(port)) and 1 <= int(port) <= 65535:
            return int(port)
        raise exceptions.IncorrectPortError

    @staticmethod
    def recipients_addresses_parser(addresses_list):
        email_regex = re.compile(r'.+@.+\..+\n*')
        empty_line = re.compile(r'(\n|\s|\a|\t)+\n*')
        if len(addresses_list) == 1 and addresses_list[0][0] == '@':
            filename = addresses_list[0][1:]
            list_of_line = []
            failed_line = 0

            with open(Path(filename), 'r') as file:
                for line in file:
                    failed_line += 1
                    if email_regex.fullmatch(line):
                        list_of_line.append(line.strip())
                    elif empty_line.fullmatch(line):
                        continue
                    else:
                        raise exceptions.IncorrectRecipientAddressError(
                            failed_line, True)

                if not list_of_line:
                    raise exceptions.NotEnteredRecipientsError

            return list_of_line
        else:
            failed_address = 0

            for address in addresses_list:
                failed_address += 1

                if not email_regex.fullmatch(address):
                    raise exceptions.IncorrectRecipientAddressError(
                        failed_address)

            return addresses_list

    @staticmethod
    def extract_subject_message(subject_list):
        subject_string = ' '.join(subject_list)

        return subject_string

    def entering_message(self):
        self.message = ''.join(sys.stdin)

    @staticmethod
    def attachment_parser(attach):
        attach_regex = re.compile(r'(.+)(?= \[\[(.+)\]\])')

        if len(attach) > 1:
            raise exceptions.IncorrectAttachError

        attach = attach[0]

        argument_string = ' '.join(attach)

        new_name = None
        attach_match = attach_regex.search(argument_string)
        if attach_match:
            pathway = attach_match.group(1)
            new_name = attach_match.group(2)

            if not Path(pathway).exists():
                raise exceptions.IncorrectFileNameError(pathway)

            return [pathway], new_name
        elif len(attach) > 1:
            raise exceptions.IncorrectAttachError

        if not Path(attach[0]).exists():
            raise exceptions.IncorrectFileNameError(attach[0])

        return attach, new_name

    def entering_password(self):
        self.sender_password = getpass.getpass('Enter sender password:')

    def entering_sender_email(self):
        for line in sys.stdin:
            self.sender_mail = line.strip()
            return


def create_argument_parser():
    description = 'This is program for mail sending.'
    epilog = ('\n\nExit code "0" - Successfully ended.\nExit code "1" - You '
              'have entered none recipients addresses.\nExit code "2" - '
              'Entered incorrect recipient address.\nExit code "3" - Entered '
              'incorrect server address.\nExit code "4" - Entered incorrect '
              'port number.\nExit code "5" - File not found.\nExit code "6" '
              '- Entered incorrect attach.'
              '\n\nOctober 2017, Ural Federal University')
    parser_help = 'Displays help information on this program.\n\n'
    sender_email = "As required param takes sender's email address.\n\n"
    server_port = ("As required param takes SMTP-server's address and,\n"
                   "if u need, entering number of server's port (by default "
                   "465): -s smtp.gmail.com:999\n\n")
    mail_topic = "As optional param takes subject of your mail.\n\n"
    zip_ = ('As optional flag-param takes "--zip", if u wanna wrap up all '
            'message in zip-archive.\n\n')
    debug = ('As optional flag-param takes "--debug", if u wanna display '
             'dialog with server.\n\n')
    attach = ('As optional param takes pathway to file, which u wanna attach '
              'to message.\nAlso u can set filename for sending: file.txt ['
              'new filename]\n\n')
    attaches = ('As optional param takes string with pathways (without '
                'spaces) to files,\nwhich u wanna attach to message: file1 '
                'file2 file3\n\n')
    open_sending = ('As optional flag-param takes "--open-sending", '
                    'if u wanna all recipients can see each other.\n\n')
    max_size = ("As optional param takes integer number - maximum kilobytes in"
                " message's attaches.\n\n")
    mail_to = ('As required param takes receivers emails:\none@two.com '
               'three@four.com five@six.com\n..or pathway to file with all '
               'recipients addresses (in each line one address):\n@filename')

    parser = argparse.ArgumentParser(
        prog='SmtpClient',
        description=description,
        epilog=epilog,
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter
    )
    param_group = parser.add_argument_group(
        title='Launch params'
    )
    param_group.add_argument(
        'sender_email',
        nargs=1,
        type=str,
        help=sender_email
    )
    param_group.add_argument(
        '--help', '-h',
        action='help',
        help=parser_help
    )
    param_group.add_argument(
        '--server-port', '-s',
        type=str,
        help=server_port,
        required=True
    )
    param_group.add_argument(
        '--mail-topic', '-t',
        default='',
        nargs='+',
        type=str,
        help=mail_topic,
        metavar=''
    )
    param_group.add_argument(
        '--zip', '-z',
        action='store_true',
        help=zip_
    )
    param_group.add_argument(
        '--debug', '-d',
        action='store_true',
        help=debug
    )
    param_group.add_argument(
        '--attach',
        type=str,
        action='append',
        nargs='+',
        help=attach,
        metavar=''
    )
    param_group.add_argument(
        '--attaches',
        type=str,
        nargs='+',
        help=attaches,
        metavar=''
    )
    param_group.add_argument(
        '--open-sending', '-o',
        action='store_true',
        help=open_sending
    )
    param_group.add_argument(
        '--max-size',
        type=int,
        default=None,
        help=max_size,
        metavar=''
    )
    param_group.add_argument(
        '--mail-to', '-m',
        type=str,
        nargs='+',
        help=mail_to,
        required=True
    )
    return parser


def input_data():
    parser = create_argument_parser()
    namespace = parser.parse_args()
    entered_data = EnteredData(namespace)
    entered_data.entering_password()
    entered_data.entering_message()

    return entered_data
