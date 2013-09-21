piconga
=======

PiConga is a messaging system for Raspberry Pi which sends a message around a loop (or Conga) of Pis.  It is primarily aimed to be a teaching aid for use with Pis.

Distributing Pis and getting them used by children is challenging for a number of reasons.

1. Getting started (particularly in schools) can be difficult because few Network Managers are happy with Pis simply being plugged into the school network.
2. There is a confidence “hurdle” to be crossed in getting children to write a program or change an existing one as this is something which is quite unusual for them to do these days with the computers that they come across.
3. With some of the basic Pi functions there’s a “So what?” question that needs to be answered - printing a “hello world” message just isn’t that exciting. It’s a great bit of kit but it is, as everyone recognises, just a low power computer so getting it to do something useful and engaging can be challenging.

The idea is to provide an application which connects Pis in a ring (the Conga). Children can then send messages around the Conga and the messages would be displayed to everyone in the Conga. They would typically start by having these Congas in their classrooms on a dedicated network, i.e. not the school network – rather all the Pis would be joined by a single, cheap router. This would be overseen by a teacher to get things started but then the fun really starts when they read the code and try to change it.

Read the [PiConga Home](https://github.com/neilcollins/piconga/wiki/Home) page in the Wiki for more details.

Proposed phasing:
* Phase 1 : create a Web App to co-ordinate Pi registration and form into a loop.
* Phase 2 : run Web App on Web Server (maybe Amazon)
* Phase 3 : basic send/receive of message around a loop of Pis using this server
* Phase 4 : add facility for an ad hoc mode which discovers other Pis on the network
* Phase 5 : add in a load of Easter eggs for intrepid coders to find

We are currently on phase 3 of the project.
