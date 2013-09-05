# -*- coding: utf-8 -*-
"""
tornado_server.conga
~~~~~~~~~~~~~~~~~~~~

Provides an abstraction of a single Conga on the Tornado Server. Each Conga
object provides detailed knowledge of how Congas are constructed from
Participants.
"""


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

    def join(self, participant, participant_id):
        """
        Have a participant join this Conga. Their position in the Conga is
        defined by their participant_id.

        Functions by finding the correct place for the participant in the
        conga. Finds the participants who will logically come before and after
        the new participant. Changes people's destinations.
        """
        # Special case: the first person joining a conga. Just add them to the
        # list and move on.
        if not self.participants:
            self.participants.append((participant_id, participant))
            return

        # Special case: usually participants will join in ascending participant
        # ID order. Check for that possibility first.
        tail_id = self.participants[-1][0]

        if tail_id < participant_id:
            prev = self.participants[-1][1]
            next = self.participants[0][1]

            self.participants.append((participant_id, participant))
        else:
            # Walk the list until we find someone whose participant ID is
            # larger than the joining person's.
            for index, person in enumerate(self.participants):
                if person[0] > participant_id:
                    break

            # Get the previous and next participants.
            prev_id, prev = self.participants[index - 1]
            next_id, next = self.participants[index]

            # Confirm that neither ID is the same as ours. That would be bad.
            if participant_id in (prev_id, next_id):
                raise RuntimeError("Identical participant IDs: %s" % participant_id)

            # Insert ourselves into the participant list.
            self.participants.insert(index, (participant_id, participant))

        # Line the participants up.
        prev.add_destination(participant)
        participant.add_destination(next)

        return
