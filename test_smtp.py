import unittest
import entering_data
import exceptions
import sending_message
import files_work
import base64
import tempfile
import os
import pathlib
import contextlib


class Client:
    def __init__(self, server_responses):
        self.server_responses = server_responses
        self.sended_command = None

    def sendall(self, command):
        self.sended_command = command

    @staticmethod
    def receive_server_response(client):
        return client.server_responses[client.sended_command]


class EnteredData:
    def __init__(self):
        self.server_name = 'server_name'
        self.port_number = 465
        self.sender_mail = 'sender_email'
        self.sender_password = 'password'
        self.recipients_list = ['recipient']
        self.mail_subject = ''
        self.message = ''
        self.attachments_list = []
        self.new_attach_name = None
        self.zip = False
        self.debug = False
        self.open_sending = False
        self.max_size = None
        self.zip_file_content = None


class Tests(unittest.TestCase):
    @staticmethod
    def patch(client, entered_data):
        instance = sending_message.receive_server_response
        sending_message.receive_server_response = \
            client.receive_server_response

        sending_message.commands_sending(client, entered_data)

        sending_message.receive_server_response = instance

    @staticmethod
    def server_response_create(entered_data):
        email = base64.b64encode(entered_data.sender_mail.encode())
        password = base64.b64encode(entered_data.sender_password.encode())
        mime_message = (sending_message.mime_message_create(entered_data) +
                        b'\r\n')
        return {b'EHLO server_name\r\n': "250 server's response",
                b'AUTH LOGIN\r\n': "334 server's response",
                email + b'\r\n': "334 server's response",
                password + b'\r\n': "235 server's response",
                'MAIL FROM:<{}>\r\n'.format(
                    entered_data.sender_mail).encode():
                        "250 server's response",
                'RCPT TO:<{}>\r\n'.format(
                    entered_data.recipients_list[0]).encode():
                        "250 server's response",
                b'DATA\r\n': "354 server's response",
                mime_message: "250 server's response",
                b'QUIT\r\n': "221 server's response"}

    def test_check_server(self):
        right_server_address = 'smtp.gmail.com'
        wrong_server_address = 'wrong_add'
        self.assertEqual(
            entering_data.EnteredData.check_server(right_server_address),
            right_server_address
        )
        with self.assertRaises(exceptions.IncorrectServerError):
            entering_data.EnteredData.check_server(wrong_server_address)

    def test_check_port(self):
        right_port = 587
        wrong_port = 'wrong_port'
        self.assertEqual(
            entering_data.EnteredData.check_port(right_port),
            right_port
        )
        with self.assertRaises(exceptions.InputDataExceptions):
            entering_data.EnteredData.check_port(wrong_port)

    def test_required_args(self):
        with self.assertRaises(SystemExit):
            with tempfile.TemporaryFile('w') as err_file:
                with contextlib.redirect_stderr(err_file):
                    entering_data.EnteredData(
                        entering_data.create_argument_parser().parse_args()
                    )

    def test_addresses_parser(self):
        right_addresses = ['receiver.first@yandex.ru',
                           'receiver.second@gmail.com']
        wrong_addresses = ['wrong_address.', 'receiver.second@gmail.com']

        self.assertEqual(
            entering_data.EnteredData.recipients_addresses_parser(
                right_addresses),
            right_addresses
        )

        with self.assertRaises(exceptions.IncorrectRecipientAddressError):
            entering_data.EnteredData.recipients_addresses_parser(
                wrong_addresses)

    def test_extract_subject(self):
        right_subject = ["It", "is", "correct", "message's", "subject."]

        self.assertEqual(
            entering_data.EnteredData.extract_subject_message(right_subject),
            ' '.join(right_subject)
        )

    def test_attachment_parser(self):
        right_attach = [['C:\\attachment', '[[filename', 'with',
                        'whitespace.txt]]']]

        with self.assertRaises(exceptions.IncorrectFileNameError):
            entering_data.EnteredData.attachment_parser(right_attach)

        with tempfile.NamedTemporaryFile('rb') as file:
            temp_name = file.name
        pathlib.Path.touch(pathlib.Path(temp_name))

        self.assertEqual(
            ([temp_name], None),
            entering_data.EnteredData.attachment_parser([[temp_name]]))

    def test_server_exception(self):
        server_responses = {b'EHLO server_name\r\n': '500 Some kind of '
                                                     'exception.'}
        client = Client(server_responses)

        instance = sending_message.receive_server_response
        sending_message.receive_server_response = \
            client.receive_server_response

        with self.assertRaises(exceptions.ServerException):
            sending_message.commands_sending(client, EnteredData())

        sending_message.receive_server_response = instance

    def test_send_empty_message(self):
        entered_data = EnteredData()
        client = Client(self.server_response_create(entered_data))
        self.patch(client, entered_data)

    def test_send_attach(self):
        entered_data = EnteredData()
        entered_data.open_sending = True
        entered_data.max_size = 100
        entered_data.new_attach_name = 'new_name'

        with tempfile.NamedTemporaryFile() as temp_file:
            temporary_name = os.path.basename(pathlib.Path(temp_file.name))
        open(temporary_name, 'a').close()

        entered_data.attachments_list = [temporary_name]

        client = Client(self.server_response_create(entered_data))
        self.patch(client, entered_data)

        if pathlib.Path(temporary_name).exists():
            pathlib.Path(temporary_name).unlink()

    def test_recipients_file(self):
        with self.assertRaises(exceptions.NotEnteredRecipientsError):
            with tempfile.NamedTemporaryFile('rb') as file:
                temp_name = file.name

            pathlib.Path.touch(pathlib.Path(temp_name))
            addresses_list = ['@{}'.format(temp_name)]
            entering_data.EnteredData.recipients_addresses_parser(
                addresses_list)

        with open(pathlib.Path(temp_name), 'w') as file:
            file.write('address.right@mail.com\n\n')
        self.assertEqual(
            entering_data.EnteredData.recipients_addresses_parser(
                addresses_list), ['address.right@mail.com'])

        pathlib.Path.unlink(pathlib.Path(temp_name))

    def test_check_correct_zip(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            temporary_name = os.path.basename(pathlib.Path(
                temp_file.name))
        pathlib.Path.touch(pathlib.Path(temporary_name))

        entered_data = EnteredData()
        entered_data.new_attach_name = 'new_name'
        entered_data.attachments_list = [temporary_name]
        files_work.zip_archiving(entered_data)
        entered_data.new_attach_name = None
        files_work.zip_archiving(entered_data)

        pathlib.Path.unlink(pathlib.Path(temporary_name))


if __name__ == '__main__':
    unittest.main()
