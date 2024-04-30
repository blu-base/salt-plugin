#!/usr/bin/env python -u

import logging
import os
import stat
import sys
import gzip
import base64
import io

from pepper import Pepper
from pepper.exceptions import PepperException

from common import DataItem, parse_data, sanitize_dict

# Configure the logging system
log = logging.getLogger(__name__)

console = logging.StreamHandler()
console.setStream(sys.stderr)

log.addHandler(console)


def compress_file(file_obj, compresslevel=9, chunk_size=1048576):
    """
    Copied from saltstack's salt.utils.gzip_util.compress_file

    Generator that reads chunk_size bytes at a time from a file/filehandle and
    yields the compressed result of each read.

    .. note::
        Each chunk is compressed separately. They cannot be stitched together
        to form a compressed file. This function is designed to break up a file
        into compressed chunks for transport and decompression/reassembly on a
        remote host.

    :param file_obj: The file object or path to the file to be compressed.
    :type file_obj: file or str
    :param compresslevel: The compression level, ranging from 0 to 9. Defaults to 9.
    :type compresslevel: int, optional
    :param chunk_size: The size of each chunk to read and compress, in bytes. Defaults to 1048576 (1MB).
    :type chunk_size: int, optional
    :return: The compressed data chunk.
    :rtype: bytes
    """
    try:
        bytes_read = int(chunk_size)
        if bytes_read != chunk_size:
            raise ValueError
    except ValueError:
        raise ValueError("chunk_size must be an integer")
    try:
        while bytes_read == chunk_size:
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=compresslevel) as gzipf:
                try:
                    bytes_read = gzipf.write(file_obj.read(chunk_size))
                except AttributeError:
                    # Open the file and re-attempt the read
                    file_obj = open(file_obj, "rb")
                    bytes_read = gzipf.write(file_obj.read(chunk_size))
            yield buf.getvalue()
    finally:
        try:
            file_obj.close()
        except AttributeError:
            pass


def file_mode(path):
    """
    Get mode from path.

    Returns file permissions including the sticky bit as integer

    :param path: The path to the file.
    :type path: str
    :return: The file permissions.
    :rtype: int
    """
    try:
        return int(oct(stat.S_IMODE(os.stat(path).st_mode)))
    except (TypeError, IndexError, ValueError):
        return None


def main():
    """
    Main function to execute the file transfer via Salt-API

    This function retrieves necessary data from environment variables provided by Rundeck.
    """
    # parse environment provided by rundeck
    data_items = [
        DataItem('host', 'RD_NODE_HOSTNAME', 'str'),
        DataItem('src', 'RD_FILE_COPY_FILE', 'str'),
        DataItem('dest', 'RD_FILE_COPY_DESTINATION', 'str'),
        DataItem('chunk-size', 'RD_CONFIG_SALT_FILE_COPY_CHUNK_SIZE', 'int'),
        DataItem('url', 'RD_CONFIG_URL', 'str'),
        DataItem('eauth', 'RD_CONFIG_EAUTH', 'str'),
        DataItem('user', 'RD_CONFIG_USER', 'str'),
        DataItem('password', 'RD_CONFIG_PASSWORD', 'str'),
        DataItem('verify_ssl', 'RD_CONFIG_VERIFYSSL', 'bool'),
        DataItem('log-level', 'RD_JOB_LOGLEVEL', 'str'),
    ]
    data = parse_data(data_items)
    log.debug(f"Data: {sanitize_dict(data, ['password'])}")

    # use rundeck's log level if defined
    if data['log-level'] == 'DEBUG':
        log_level = 'DEBUG'
    else:
        log_level = 'ERROR'
    log.setLevel(logging.getLevelName(log_level))

    # Output the destination path as first line of stdout
    # as specified in the documentation for a script file copier plugin
    print(data['dest'] if data['dest'] is not None else "")

    # Sanity checks for required input
    for key in ['host', 'src', 'dest', 'url', 'eauth', 'user', 'password']:
        if not data[key]:
            msg = f'No {key} specified. File not sent.'
            log.error(msg)
            print(msg, file=sys.stderr)
            sys.exit(1)

    # making sure the source can be read
    src = os.path.normpath(data['src'])

    if os.path.exists(src) and \
            os.path.isfile(src) and \
            os.access(src, os.R_OK):

        log.debug(f'Normalized source path is: {src}')
    else:
        log.error(f'The specified source file is not readable: {data["src"]}')
        sys.exit(1)

    dest = os.path.normpath(data['dest'])
    log.debug(f'Normalized destination path is: {dest}')

    # set default chunk-size if not provided
    if data['chunk-size'] is None or data['chunk-size'] == "":
        data['chunk-size'] = 1048576
    log.debug(f'Chunk-size: {data["chunk-size"]}')

    # login to the API
    client = Pepper(api_url=data['url'], ignore_ssl_errors=not data['verify_ssl'])
    try:
        response = client.login(username=data['user'], password=data['password'], eauth=data['eauth'])
    except PepperException as exception:
        print(str(exception))
        sys.exit(1)
    log.debug(f'Logging into API: {response}')

    for index, chunk in enumerate(compress_file(src, chunk_size=data['chunk-size']), start=1):
        chunk = base64.b64encode(chunk).decode('ascii')
        append = index > 1

        # arguments for cp.recv_chunked, gzipped
        args = [dest, chunk, append, True, file_mode(src)]

        # payload
        low_state = {
            'client': 'local',
            'tgt': data['host'],
            'fun': 'cp.recv_chunked',
            'arg': args,
            'full_return': True,  # full return to get retcode
        }

        log.debug(f'Low state Payload: {low_state}')

        # send payload
        try:
            response = client.low(lowstate=[low_state])
        except PepperException as exception:
            print(str(exception))
            sys.exit(1)
        log.debug(f'Received raw response: {response}')

        # filter response
        minion_response = response.get('return', [{}])[0].get(data['host'], {})
        return_code = minion_response.get('retcode', 1)

        if return_code != 0:
            # Publish failed
            log.critical(
                "Publish failed.{} It may be necessary to "
                "decrease the chunk-size (current value: "
                "{})".format(
                    " File partially transferred." if index > 1 else "",
                    data['chunk-size'],
                )
            )
            sys.exit(return_code)

    sys.exit(0)


if __name__ == '__main__':
    main()
