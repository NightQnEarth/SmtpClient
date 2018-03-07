import zipfile
import shutil
import os
import pathlib
import base64
import tempfile
import exceptions


def zip_archiving(entered_data):
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            temporary_name = '{}.zip'.format(os.path.basename(temp_file.name))

        with zipfile.ZipFile(temporary_name, 'w') as zip_archive:
            if entered_data.new_attach_name:
                if not pathlib.Path(entered_data.attachments_list[0]).exists():
                    raise exceptions.IncorrectFileNameError(
                        entered_data.attachments_list[0])
                folder_name = pathlib.Path(temporary_name[:-4])
                pathlib.Path.mkdir(folder_name)
                path_to_file = os.path.join(folder_name,
                                            entered_data.new_attach_name)
                shutil.copyfile(entered_data.attachments_list[0], path_to_file)

                zip_archive.write(path_to_file,
                                  arcname=entered_data.new_attach_name)

                if pathlib.Path(folder_name).exists():
                    shutil.rmtree(folder_name)
            else:
                for attachment in entered_data.attachments_list:
                    if not pathlib.Path(attachment).exists():
                        raise exceptions.IncorrectFileNameError(attachment)
                    zip_archive.write(pathlib.Path(attachment),
                                      os.path.basename(
                                          pathlib.Path(attachment)))

        with open(temporary_name, 'rb') as file:
            content = file.read()

        if pathlib.Path(temporary_name).exists():
            pathlib.Path(temporary_name).unlink()
    except (IOError, FileNotFoundError, FileExistsError) as exception:
        raise exceptions.FileError(
            '{}: {}'.format(type(exception), exception))

    return content


def file_division(filename, max_size, zip_content):
    def content_division(file_content):
        if len(file_content) > max_size * 1024:
            result_parts = []
            parts_count = len(file_content) // (max_size * 1024)

            for p in range(parts_count):
                part_begin = max_size * 1024 * p
                part_end = max_size * 1024 * (p + 1) - 1
                result_parts.append(file_content[part_begin:part_end])

            if len(file_content) - 1 >= max_size * 1024 * parts_count:
                result_parts.append(
                    file_content[max_size * 1024 * parts_count:])

            return result_parts

    if not zip_content:
        if not pathlib.Path(filename).exists():
            raise exceptions.IncorrectFileNameError(filename)
        try:
            with open(filename, 'rb') as file:
                file_content = base64.b64encode(file.read())
        except (IOError, FileNotFoundError, FileExistsError) as exception:
            raise exceptions.FileError(
                '{}: {}'.format(type(exception), exception)
            )
    else:
        file_content = zip_content

    return content_division(file_content) or [file_content]


def files_groups_for_sending_create(entered_data):
    filename_with_parts_of_file = {}

    for attachment in entered_data.attachments_list:
        filename_with_parts_of_file[attachment] = \
            file_division(attachment, entered_data.max_size,
                          entered_data.zip_file_content)

    normal_size_files = {}
    for filename in filename_with_parts_of_file:
        if len(filename_with_parts_of_file[filename]) == 1:
            normal_size_files[filename] = \
                filename_with_parts_of_file[filename]
            filename_with_parts_of_file[filename] = None

    if normal_size_files:
        normal_size_files = sorted(
            normal_size_files.items(), key=lambda t: len(t[1][0]))

    files_groups = []

    for filename in filename_with_parts_of_file:
        if filename_with_parts_of_file[filename]:
            for part in filename_with_parts_of_file[filename]:
                files_groups.append({filename: part})

    size = 0
    group = dict()
    for _tuple in normal_size_files:
        size += len(_tuple[1][0])
        if size <= entered_data.max_size * 1024:
            group[_tuple[0]] = _tuple[1][0]
        else:
            files_groups.append(group)
            group = {_tuple[0]: _tuple[1][0]}
            size = len(_tuple[1][0])

    if group:
        files_groups.append(group)

    return files_groups
