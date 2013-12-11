# -*- coding: utf-8 -*-
"""
tornado_server.conga
~~~~~~~~~~~~~~~~~~~~

Provides an abstraction of a single Conga on the Tornado Server. Each Conga
object provides detailed knowledge of how Congas are constructed from
Participants.
"""
import logging
import random
from tornado_exceptions import JoinError, LeaveError


__congas = {}


def conga_from_id(conga_id):
    """
    Given a conga_id, returns the corresponding Conga object.
    """
    try:
        conga = __congas[conga_id]
    except KeyError:
        conga = Conga(conga_id)
        __congas[conga_id] = conga

    return conga


class Conga(object):
    """
    An object representing a single Conga. A Conga is made up of multiple
    participants connected in a ring. These participants may enter or leave at
    any time. An individual connection registers to be part of a single Conga
    and is placed into the correct position in the conga based on its
    user-ID.
    """
    def __init__(self, conga_id):
        #: The ID of this conga in the DB.
        self.conga_id = conga_id

        #: A list of the participants in the conga, in their conga order. Each
        #: element of this list is a tuple of
        #: (Participant id, Participant object). This allows for linear-time
        #: insertion of and removal of conga participants.
        self.participants = []

        # A dict of the outstanding messages being sent around the conga, and
        # the participant ID that sent them. Used to prevent a message looping
        # forever.
        self.outstanding_messages = {}

    def join(self, participant, participant_id):
        """
        Have a participant join this Conga. Their position in the Conga is
        defined by their participant_id.

        Functions by finding the correct place for the participant in the
        conga. Finds the participants who will logically come before and after
        the new participant. Changes people's destinations.
        """
        logging.info("Participant id %d joining." % participant_id)

        # Special case: the first person joining a conga. Just add them to the
        # list and move on.
        if not self.participants:
            logging.info("No participants.")
            self.participants.append((participant_id, participant))

            # Point the participant at self initially.
            participant.add_destination(participant)
            return

        # Special case: usually participants will join in ascending participant
        # ID order. Check for that possibility first. Then, check whether we're
        # at the start of the list as well.
        tail_id = self.participants[-1][0]

        if tail_id < participant_id:
            logging.info("At start.")
            prev = self.participants[-1][1]
            next = self.participants[0][1]

            self.participants.append((participant_id, participant))
        else:
            # Walk the list until we find someone whose participant ID is
            # larger than the joining person's.
            for index, person in enumerate(self.participants):
                if person[0] > participant_id:
                    logging.info("Found insert index: %d" % index)
                    break

            # Get the previous and next participants.
            if index == 0:
                prev_id, prev = self.participants[-1]
            else:
                prev_id, prev = self.participants[index - 1]

            next_id, next = self.participants[index]

            # Confirm that neither ID is the same as ours. That would be bad.
            if participant_id in (prev_id, next_id):
                logging.error(
                    "Attempted to add duplicate participant %s in %s." %
                    (participant_id, self.conga_id)
                )
                raise JoinError(
                    "Identical participant IDs: %s" % participant_id
                )

            # Insert ourselves into the participant list.
            self.participants.insert(index, (participant_id, participant))

        # Line the participants up.
        prev.add_destination(participant)
        participant.add_destination(next)

        return

    def leave(self, participant, participant_id):
        """
        Have a particular participant leave this Conga. Their position in this
        conga is defined by their participant ID.

        Finds the participant in the current conga. Takes the person before
        them and sets their new target to the person after them.
        """
        logging.info("Participant id %d leaving." % participant_id)

        # Find the participant.
        match = False

        # There's a special case here: if the conga has only one participant.
        # Handle that case.
        if len(self.participants) == 1:
            logging.info("One participant.")
            self.participants.pop()
            return

        for index, person in enumerate(self.participants):
            if person[0] == participant_id:
                logging.info("Match at index %d, id %d" % (index, person[0]))
                match = True
                break

        if not match:
            # Called on an incorrect conga. Log and bail early.
            logging.error(
                "Attempted to remove participant %s from incorrect conga %s." %
                (participant_id, self.conga_id)
            )
            raise LeaveError("Not in conga.")

        if person == self.participants[0]:
            # Special case: participant at 'start' of Conga.
            logging.info("Start of conga.")
            prev = self.participants[-1][1]
            next = self.participants[1][1]
        elif person == self.participants[-1]:
            # Special case: person at 'end' of Conga.
            logging.info("End of conga.")
            prev = self.participants[-2][1]
            next = self.participants[0][1]
        else:
            # Standard case.
            logging.info("Normal.")
            prev = self.participants[index - 1][1]
            next = self.participants[index + 1][1]

        # Remove from message path.
        prev.add_destination(next)

        # Remove from the participant list.
        self.participants.pop(index)

        return

    def new_message(self, participant_id):
        """
        Notify the conga about a new message.  Should be called whenever a
        message is received without a Message-ID header. Returns the ID to give
        that message.
        """
        msg_id = '%10d' % (random.randint(1, 4294967296)) # From 1 to 2^32.
        msg_id = msg_id.strip()
        self.outstanding_messages[msg_id] = participant_id
        logging.info(
            "Added new message: ID %s, Participant %s." % (
                msg_id,
                participant_id
            )
        )
        return msg_id

    def stop_loop(self, msg_id, participant_id):
        """
        Check with the conga whether the message currently looping around the
        conga has reached the participant who originally sent it. Returns
        True if the message should be prevented from looping further, or False
        if it's safe to send to this participant.

        This will also confirm that the participant who originally sent
        the message is still in the conga. If they aren't, the message will
        be stopped immediately.
        """
        # First, check whether the participant who sent the message is the
        # one we're about to send to.
        msg_id = msg_id.strip()
        print self.outstanding_messages

        try:
            original_sender_id = self.outstanding_messages[msg_id]
        except KeyError:
            # Unknown message ID. Kill it with fire.
            logging.info("Unknown message ID %s" % msg_id)
            return True

        if original_sender_id == participant_id:
            logging.info("Message returning to original sender.")
            del self.outstanding_messages[msg_id]
            return True

        # Next, confirm the original sender is still in the conga.
        for pid in (participant[0] for participant in self.participants):
            if pid == original_sender_id:
                logging.info("Original sender still in Conga")
                return False

        # If we got here the original sender has gone: terminate the message.
        logging.info("Original sender no longer in conga.")
        del self.outstanding_messages[msg_id]
        return True
