# Autoharmonize Engineering Notebook
## CS 262 Final Project
### Ari Troper, Liam McInroy, & Max Snyder

This document contains a few random bits of information.
It may be debugging information, designs, or general nonsense that happens
during development.

This isn't the "final writeup" of the project... that will come in time.

## Design

### Startup protocol

We don't want a "group handshake" at the start, rather we want to allow people
to "join and leave" the symfony / jam session at will.

The rough outline of the protocol is:

- (i) each machine has an "incoming" socket, so that they
may block on pairwise communication of messages (for acknowledgements). Then
each pair of machines will have a connection to and from each other on these
different sockets.

- (ii) a machine starts up. Its "incoming" socket address and port must be
known by the next machine that starts up.

- (iii) the not-first machine connects to an "incoming" socket. It
sends its own "incoming" socket information, so that the bidirectional
connection may be established. The machine it connects to sends all other
machines which it is connected to, so that it may create pairwise connections
with each other machine.

### Synchronization protocol

The problem is streaming audio.
There's a couple of features we would like to support which are a bit unique
to this style of time-series.

- F1. Play

- F2. Pause

- F3. Seek
