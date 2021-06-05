# -*- coding: utf-8 -*-

"""
Copyright (C) 2021, Zato Source s.r.o. https://zato.io

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

# stdlib
from datetime import datetime
from logging import getLogger
from tempfile import NamedTemporaryFile
from time import time
from traceback import format_exc

# Bunch
from bunch import bunchify

# gevent
from gevent.server import StreamServer

# pysimdjson
from simdjson import Parser as SIMDJSONParser

# Zato
from zato.common.api import SFTP
from zato.common.json_internal import dumps
from zato.common.sftp import SFTPOutput
from zato.common.events.common import Action
from zato.common.util.tcp import ZatoStreamServer
from zato.server.connection.connector.subprocess_.base import BaseConnectionContainer, Response
from zato.server.connection.connector.subprocess_.impl.events.database import EventsDatabase

# ################################################################################################################################
# ################################################################################################################################

if 0:
    from bunch import Bunch
    from socket import socket

    Bunch = Bunch
    socket = socket

# ################################################################################################################################
# ################################################################################################################################

logger = getLogger('zato_events')

# ################################################################################################################################
# ################################################################################################################################

# For later use
utcnow = datetime.utcnow

# ################################################################################################################################
# ################################################################################################################################

class EventsConnectionContainer(BaseConnectionContainer):

    connection_class = object
    ipc_name = conn_type = logging_file_name = 'events'

    remove_id_from_def_msg = False
    remove_name_from_def_msg = False

# ################################################################################################################################

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        fs_data_path = '/tmp/zzz-parquet'
        sync_threshold = 10_000
        sync_interval_ms = 120_000

        # This is where events are kept
        self.events_db = EventsDatabase(fs_data_path, sync_threshold, sync_interval_ms)

        # By default, keep running forever
        self.keep_running = True

        # A reusable JSON parser
        self._json_parser = SIMDJSONParser()

        # Map handler names to actual handler methods
        self._action_map = {
            Action.Ping: self._on_event_ping,
            Action.Push: self._on_event_push,
        }

# ################################################################################################################################

    def _on_event_ping(self, ignored_data, address_str):
        # type: (bystr, str) -> str
        logger.info('Ping received from `%s`', address_str)
        return Action.PingReply

# ################################################################################################################################

    def _on_event_push(self, data, address_str):
        # type: (str, str) -> str

        # We received JSON bytes so we now need to load a Python object out of it ..
        data = self._json_parser.parse(data)
        data = data.as_dict() # type: dict

        # .. now, we can push it to the database.
        self.events_db.push(data)

# ################################################################################################################################

    def _on_new_connection(self, socket, address):
        # type: (socket, str) -> None

        # For later use
        address_str = '{}:{}'.format(address[0], address[1])

        # A new client connected to our server
        logger.info('New stream connection from %s', address_str)

        # Get access to the underlying file object
        socket_file = socket.makefile(mode='rb')

        # Keep running until explicitly requested not to
        while self.keep_running:

            # We work on a line-by-line basis
            line = socket_file.readline()

            # No input = client is no longer connected
            if not line:
                logger.info('Stream client disconnected (%s)', address_str)
                break

            # Extract the action sent ..
            action = line[:2]

            # .. find the handler function ..
            func = self._action_map.get(action)

            # .. no such handler = disconnect the client ..
            if not func:
                logger.warn('No handler for `%r` found. Disconnecting stream client (%s)', action, address_str)
                break

            # .. otherwise, handle the action ..
            data = line[2:]
            response = func(data, address_str) # type: str

            # .. not all actions will result in a response ..
            if response:
                response = response.encode('utf8') if isinstance(response, str) else response

                # .. now, we can send the response to the client.
                socket.sendall(response)

        # If we are here, it means that the client disconnected.
        socket_file.close()

# ################################################################################################################################

    def make_server(self):
        return ZatoStreamServer((self.host, self.port), self._on_new_connection)

# ################################################################################################################################
# ################################################################################################################################

if __name__ == '__main__':

    container = EventsConnectionContainer()
    container.run()

# ################################################################################################################################
# ################################################################################################################################
