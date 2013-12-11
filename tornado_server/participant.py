# -*- coding: utf-8 -*-
"""
tornado_server.participant
~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines the representation of a single participant in a conga.
"""
from tornado.iostream import StreamClosedError
from conga import Conga, conga_from_id
from tornado_exceptions import JoinError, LeaveError
from decorators import bye_on_error, bye_on_error_cb
import logging
import traceback
# Define some states for the Participant connection.
OPENING = 0
UP = 1
CLOSING = 2


class Participant(object):
    """
    Participant wraps a single incoming IOStream. It knows about the next
    participant in the Conga chain, and correctly writes to it.
    """
    def __init__(self, source, db):
        #: The tornado IOStream socket wrapper pointing to the end user.
        self.source_stream = source

        #: The Participant object representing the next link in the conga.
        self.destination = None

        #: A reference to the database object.
        self.db = db

        #: An indiciation of the state of this connection.
        self.state = OPENING

        #: The ID of this particular conga participant.
        self.participant_id = None

        #: The ID of the conga.
        self.conga_id = None

    @bye_on_error
    def add_destination(self, destination):
        """
        Add a new conga participant as the target for any incoming conga
        messages.
        """
        self.destination = destination

    @bye_on_error
    def write(self, data, message_id, conga):
        """
        Write data on the downstream connection. If no such connection exists,
        drop this stuff on the floor.
        """
        # Before sending this, check whether we originally sent this message.
        # If we did, don't do anything.
        if conga.stop_loop(message_id, self.participant_id):
            return

        try:
            self.source_stream.write(data)
        except AttributeError:
            pass

    @bye_on_error
    def wait_for_headers(self):
        """
        Read from the incoming stream until we receive the delimiter that tells
        us that the headers have ended.
        """
        try:
            self.source_stream.read_until(b'\r\n\r\n', self._parse_headers)
        except StreamClosedError:
            if self.state != CLOSING:
                # Unexpected closure: run the Bye logic.
                logging.error(
                    "Unexpected close by participant %d" % self.participant_id
                )
                self._bye()('')

    @bye_on_error
    def _parse_headers(self, header_data):
        """
        Turns the headers into a dictionary. Checks the content-length and
        reads that many bytes as the body. Most importantly, handles the
        request URI.
        """
        headers = {}

        decoded_data = header_data.decode('utf-8')
        lines = decoded_data.split('\r\n')
        request_uri = lines[0]

        try:
            header_lines = lines[1:]
        except IndexError:
            header_lines = []

        for line in header_lines:
            if line:
                key, val = line.split(':', 1)
                headers[key] = val

        # Get the content-length, and then read however many bytes we need to
        # get the body.
        length = int(headers.get('Content-Length', '0'))

        if (request_uri == 'HELLO') and (self.state == OPENING):
            cb = self._hello(headers)
        elif (request_uri == 'BYE') and (self.state == UP):
            cb = self._bye(headers)
        elif (request_uri == 'MSG') and (self.state == UP):
            cb = self._repeat_data(header_data, headers)
        else:
            # Unexpected verb: bail.
            logging.error(
                "Unexpected verb %s on participant %s in state %d." %
                (request_uri, self.participant_id, self.state)
            )
            self._bye()('')

        self.source_stream.read_bytes(length, cb)

        # If we're closing up shop, don't bother reading again.
        if self.state != CLOSING:
            self.wait_for_headers()

    def _hello(self, headers={}):
        """
        Builds a closure for use as a registration callback.

        Note that this closure does not take the header data but the actual
        headers dictionary. This is deliberate: we'll actually use the headers
        here, so there's no point parsing them twice.
        """
        @bye_on_error_cb(self)
        def callback(data):
            try:
                # Validate the participant against the DB.
                received_id = headers['User-ID'].strip()
                conga_id = self.db.get(
                    "SELECT conga_id FROM conga_congamember WHERE member_id=%s",
                    (received_id,)
                )[0][0]

                # At this stage we've successfully validated this participant.
                # Bring them up.
                self.participant_id = int(received_id)
                self.conga_id = conga_id
                self.state = UP

                # Join the conga.
                conga = conga_from_id(conga_id)
                conga.join(self, self.participant_id)
            except (KeyError, IndexError), e:
                # This will catch a missing User-ID as well as a failed SQL
                # lookup.
                logging.error(
                    "Hit exception %s adding participant %s to conga %s." %
                    (e, self.participant_id, self.conga_id)
                )
                logging.error(traceback.format_exc())

                self.source_stream.close()
                self.state = CLOSING
            except JoinError:
                # The attempt to join the conga failed. Close up, and
                # additionally run the BYE logic.
                self._bye()('')

        return callback

    def _bye(self, headers={}):
        """
        Builds a closure for execution on receipt of a conga BYE.
        """
        def callback(data):
            # Begin by dumping ourselves out of the conga, so that we don't
            # receive any more messages. If this fails, log the failure but
            # keep going.
            try:
                conga = conga_from_id(self.conga_id)
                conga.leave(self, self.participant_id)
            except LeaveError, e:
                logging.error(
                    "Failed to remove %s from conga %s because of %s" %
                    (self.participant_id, self.conga_id, e)
                )

            # Now remove ourselves from the DB. If it fails, just log, but keep
            # going.
            try:
                self.db.execute("DELETE FROM conga_congamember WHERE id=%s",
                                (self.participant_id,))
            except Exception, e:
                logging.error(
                    "Failed to remove %s from conga %s because of %s" %
                    (self.participant_id, self.conga_id, e)
                )

            # Finally, close the connection here.
            self.destination = None

            if not self.source_stream.closed():
                self.source_stream.close()

            self.state = CLOSING

        return callback

    def _repeat_data(self, header_data, headers):
        """
        Builds a closure for use as a data sending callback. We use a closure
        here to ensure that we are able to wait for the message body before
        sending the headers, just in case the message is ill-formed. That way
        we don't confuse clients by sending headers with no following body.
        """
        @bye_on_error_cb(self)
        def callback(data):
            # Before we start, check whether there is a Message ID on this
            # message. If there isn't, we've never seen it before.
            # Check whether this is a message we've seen before.
            conga = conga_from_id(self.conga_id)

            try:
                msg_id = headers['Message-ID']
                new_header_data = header_data
            except KeyError:
                # New message. Get a message ID for it, and then add it to the
                # header data.
                msg_id = conga.new_message(self.participant_id)
                new_header_data = header_data[:-2]
                new_header_data += 'Message-ID: %s\r\n\r\n' % (msg_id)

            dest_id = 0

            try:
                dest_id = self.destination.participant_id
                self.destination.write(new_header_data + data, msg_id, conga)
            except StreamClosedError:
                if self.destination.state != CLOSING:
                    # Unexpected closure. BYE logic has already been run by
                    # the decorator on write, so log and move on with our
                    # lives.
                    logging.error(
                        "Unexpected close by participant %d" % dest_id
                    )

        return callback
