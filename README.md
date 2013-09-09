piconga
=======

Messaging System for Raspberry Pi which sends a message around a loop (or Conga) of Pis.

Read the [PiConga Home](https://github.com/neilcollins/piconga/wiki/Home) page in the Wiki to get started. 

Proposed phasing:
* Phase 1 : basic send/receive of message around a loop of Pis which discover each other on the network
* Phase 2 : add in Web App to co-ordinate Pi registration and form into a loop.
* Phase 3 : run Web App on Web Server (maybe Amazon)
* Phase 4 : add in voice (not needed initially and possibly not at all as may be hard to use audio on the Pis).

Some high level ideas:
* use Python for everything (language of choice for GCSE and A Level students)
* allow web app to run on a Pi as well (so it you can run a loop on a standalone network)
* use JSON as protocol between Pi and Web App.
