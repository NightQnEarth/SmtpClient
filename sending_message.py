import itertools
import socket
import base64
import ssl
import os
import pathlib
import quopri
import exceptions
import files_work


def mime_message_create(entered_data, files_group=None):
    recipients_addresses = ''
    if entered_data.open_sending:
        recipients_addresses = ', '.join(entered_data.recipients_list)

    message = (
        'MIME-Version: 1.0\r\n'
        'From:{}\r\n'
        'To:{}\r\n'
        'Subject:{}\r\n'
        'Content-Type: multipart/mixed; '
        'boundary=gc0p4Jq0M2Yt08jU534c0p\r\n\r\n'
        '--gc0p4Jq0M2Yt08jU534c0p\r\n'
        'Content-Type: text/plain\r\n'
        'Content-Transfer-Encoding: quoted-printable\n\n'
        '{}'.format(
            entered_data.sender_mail,
            recipients_addresses,
            entered_data.mail_subject,
            (quopri.encodestring(entered_data.message.encode())).decode(
                'utf-8'))
    ).encode()

    if not files_group:
        for attachment in entered_data.attachments_list:
            if not pathlib.Path(attachment).exists():
                raise exceptions.IncorrectFileNameError(attachment)
            try:
                with open(attachment, 'rb') as file:
                    filename = os.path.basename(pathlib.Path(attachment))
                    if entered_data.new_attach_name and not entered_data.zip:
                        filename = entered_data.new_attach_name
                    elif entered_data.zip:
                        filename = 'attachments.zip'
                    file_content = file.read() if not entered_data.zip else \
                        entered_data.zip_file_content
                    message += (
                        '--gc0p4Jq0M2Yt08jU534c0p\r\n'
                        'Content-Type: application/octet-stream;\r\n'
                        'Content-Disposition: attachment; filename="{}"\r\n'
                        'Content-Transfer-Encoding: base64\n\n'.format(
                            filename).
                        encode() + base64.b64encode(file_content) + b'\r\n'
                    )
            except IOError as exception:
                raise exceptions.FileError(
                    '{}: {}'.format(type(exception), exception))
    else:
        for filename, file_content in files_group.items():
            if entered_data.new_attach_name and not entered_data.zip:
                filename = entered_data.new_attach_name
            elif entered_data.zip:
                filename = 'attachments.zip'
            message += (
                '--gc0p4Jq0M2Yt08jU534c0p\r\n'
                'Content-Type: application/octet-stream;\r\n'
                'Content-Disposition: attachment; filename="{}"\r\n'
                'Content-Transfer-Encoding: base64\n\n'.format(
                    os.path.basename(pathlib.Path(filename))).
                encode() + file_content + b'\r\n'
            )
    message += b'.'

    return message


def command_list_create(entered_data, already_authenticated, files_group=None):
    if already_authenticated:
        begin_part = \
            ['EHLO {}'.format(entered_data.server_name).encode(),
             'MAIL FROM:<{}>'.format(entered_data.sender_mail).encode()]
    else:
        begin_part = \
            ['EHLO {}'.format(entered_data.server_name).encode(),
             b'AUTH LOGIN',
             base64.b64encode(entered_data.sender_mail.encode()),
             base64.b64encode(entered_data.sender_password.encode()),
             'MAIL FROM:<{}>'.format(entered_data.sender_mail).encode()]

    middle_part = \
        ['RCPT TO:<{}>'.format(recipient).encode()
         for recipient in entered_data.recipients_list]

    end_part = \
        [b'DATA',
         mime_message_create(entered_data, files_group),
         b'QUIT']

    return itertools.chain(begin_part, middle_part, end_part)


def receive_server_response(client):
    with client.makefile('rb') as file_repr:
        data = []
        while True:
            line = file_repr.readline()
            data.append(line)
            if line[3:4] == b' ':
                break
        return (b''.join(data)).decode()


def debug_display(entered_data, message):
    if entered_data.debug:
        print(message)


def mail_sending(entered_data):
    with ssl.wrap_socket(socket.socket()) as client:
        client.connect((entered_data.server_name, entered_data.port_number))

        debug_display(entered_data, receive_server_response(client))

        commands_sending(client, entered_data)


def commands_sending(client, entered_data):
    send_flag = False
    attempt_count = 0
    max_attempts_count = 2
    while attempt_count <= max_attempts_count and not send_flag:
        attempt_count += 1

        if entered_data.zip:
            entered_data.zip_file_content = files_work.zip_archiving(
                entered_data)

        if entered_data.max_size:
            files_groups = files_work.files_groups_for_sending_create(
                entered_data)
        else:
            files_groups = [None]

        for group_number in range(len(files_groups)):
            already_authenticated = False if group_number == 0 else True

            for command in command_list_create(
                    entered_data, already_authenticated, files_groups[
                        group_number]):
                if (command == b'QUIT' and group_number < len(
                        files_groups) - 1):
                    command = b'RSET'

                client.sendall(command + b'\r\n')

                debug_display(entered_data, command.decode(errors='ignore'))

                server_response = receive_server_response(client)

                debug_display(entered_data, server_response)

                send_flag = True
                if (attempt_count <= max_attempts_count and
                        server_response[0:3] == '535'):
                    print('\n\rAuthentication failed: Invalid user or '
                          'password!')

                    client.sendall(b'RSET\r\n')
                    debug_display(entered_data, 'RSET')

                    server_response = receive_server_response(client)

                    debug_display(entered_data, server_response)

                    print('Enter sender login again:')
                    entered_data.entering_sender_email()
                    entered_data.entering_password()

                    send_flag = False
                    break

                if int(server_response[0]) in [4, 5]:
                    raise exceptions.ServerException(server_response)
