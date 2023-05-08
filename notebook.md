# Autoharmonize Engineering Notebook
## CS 262 Final Project
### Ari Troper, Liam McInroy, & Max Snyder

This document contains a few random bits of information.
It may be debugging information, designs, or general nonsense that happens
during development.

This isn't the "final writeup" of the project... that is in [paper/](paper/).

## Design

### Startup Protocol

We don't want a "group handshake" at the start, rather we want to allow people
to "join and leave" the synfony / jam session at will.

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
with each other's machines.

### Synchronization Protocol: High-Level

To synchronize audio across the distributed clients we devised a heartbeat-synchronization protocol: the clients are synced through a “heartbeat” which fires locally every .1 seconds. At the beginning of every heartbeat, all the clients send their “vote” for the synced state. For example, if a client turns up the volume, a vote for a volume event would be cast at the start of the next heartbeat. If a user does nothing, then a “No Event” is sent across the wire. These events also contain metadata about the channel state. Since the UI freezes after a user-triggered action by presenting a loading indicator, a user cannot submit more than one vote during the same heartbeat. The systems all wait the duration of the heartbeat to receive the votes from the other clients. It is assumed that the latency across the wires will not be longer than the length of the heartbeat. Therefore, the voting protocol will fail if and only if a client is down. Once all the votes are received by each client, a protocol runs locally to determine which events take precedence. This protocol will be discussed further in detail in the next section. Once a consensus is reached through this protocol, the state is applied, and the machines are synced.

When brainstorming the heartbeat-synchronization protocol, we also considered another solution, which we will denote the “reactive” protocol. In the reactive protocol, when a client fires a request such as a volume change, then it sends the event immediately to all the other clients. When the other clients receive the event, they will derive their next state as a function of their current state and the received event, as defined by a predetermined state machine. Once the client transitions, they will also send their current state to the other clients across the wire. These messages will continue to happen reactively, until each client has reached a terminal node in the state machine.

Specifically, the benefits of the reactive protocol over the heartbeat protocol are: 

1. Clients can retry sending their messages immediately, whereas otherwise they must wait the duration of the heartbeat

1. Latency over the network does not have to be limited by the length of the heartbeat-- in fact the latency upper bound is infinite-- since all machines will “react” once receiving a message.

1. A down client does not need to be accounted for because it does not affect the correctness of the system. If a client goes down in the reactive system, even during concurrent sends, the clients that successfully received the event message will reactively relay their states to the other up clients. However, in the heartbeat system, assuming a client could fail between concurrent sends, it becomes a challenge to relay across all the clients which “votes” to account for.

The drawbacks of the reactive protocol:

1. The clients will be out of sync until all the clients have reached a terminal node in the state machine. Depending on the network latency, this could take some significant time.

1. It is difficult to debug. Since messages happen reactively, and as a function of latency, it is difficult to reproduce behavior or predict what the correct behavior should be.

1. A state machine cannot reconcile two simultaneous seek-events. Which one would take precedence? As the clients receive the two separate seek events they will perpetually flip-flop between the two timestamps as they reactively relay their new state. To fix this issue we could introduce a seek back-off, where seek events are accepted only S seconds after accepting a previous seek event. However, this event specific behavior starts to convolute the system. 

The benefits and drawbacks described here are representative of a common distributed system tradeoff named the CAP theorem. This asserts that a distributed system can only achieve two of the following: “consistency” (every response is “correct”), “availability” (every request receives a response), and “partition tolerance” (the system is operational in spite of network failure). For this product, “correctness” in consistency means that every response is representative of the latest global state of consensus.

In general, the benefit of the reactive protocol over the heartbeat protocol is availability/partition tolerance rather than availability/consistency However, for our particular vision of the product, we prioritized consistency over availability and partition tolerance, so the heartbeat protocol was preferable.

Moreover, the heartbeat system was easier to implement and debug, which was important to consider for the time window we had to work.

### Synchronization Protocol

The problem is streaming audio.
There's a couple of features we would like to support which are a bit unique
to this style of time-series (really, its anything data that is
time-series-esque, where there may be arbitrary jumps, starts and stops in
"time").

- F1. Play

- F2. Pause

- F3. Seek

These are all user events, which then dictate the progression of time for
the data. We are (for now) neglecting the "streaming data" problem, that can
be safely disentangled from the "synchronization" problem in this framework.

There is a neat "reactive" protocol that would work for synchronizing these
user events (it is basically logical clocks but with a state machine, where
the consensus is based on a choice function that is deterministic and not just
majority-rule), but that seems a lil risky to implement (according to some
team members), so we are opting for the more standard "handshake" consensus.

## Implementation

### Audio Streaming

At a high level, audio streaming entails playback of audio files at timestamps specified by the protocol. There are several use-cases of audio streaming that we consider:

1. Synchronized playback of a local audio file across multiple clients. This use-case is applied to technologies such as Spotify Party (assuming the content is downloaded on each client), where participants connected to the party can each independently control the playback of the audio and the changes are synced to the other participants.

1. Synchronized playback of multiple local audio “stem files” across multiple clients. “Stem files” refer to the different parts of the arrangement, such as the drums or the vocals. The technology is the exact same as the technology referred to in 1, however this use case allows co-located speakers to create a surround sound system where, for example, the bass is playing in one corner of the room while the drums play in another corner of the room creating a fully immersive audio experience™.

1. In the case that all audio-stems are located locally on all the computers, another use case worth mentioning is the ability to “mix” audio across multiple co-located speakers. This might be useful in the case of a concert, where an audio-engineer might want to mix the volume level of each channel (drums, vocals, bass, etc.).

1. The next iteration of the technology is the ability to stream chunks of audio data from one client to another for “peer-to-peer” audio playback. This allows each client to host a different stem, but when connected to one another, each client can playback and sync the entire audio file as in Example 1. This technology further expands on Examples 1-3 because the system must now have a protocol to adjust for the latency it will take to request new chunks of audio data. The hosting and remote streaming capabilities, as well as adjustment for buffering, are necessary for a progression to Example 5. In addition, this technology could be applied to a “BitTorrent” protocol for music streaming.

1. The final iteration of this technology is live audio streaming and syncing, seen in applications such as Zoom. In this case, as in Example 4, chunks of audio data are sent and synced from one client to another. However, unlike Example 3, the audio chunks are generated in real-time. This could be, for example, from a microphone. When expanded to support MIDI data, this technology could also support virtual “jam sessions,” in which multiple musicians can all play on MIDI devices simultaneously in a simulated co-located setting.

To support audio streaming, we used the PyGame library’s Mixer module. This enabled playback of “sounds” on multiple “channels,” or concurrent audio streams. A limitation of this module is that sounds cannot be arbitrarily “seeked” -- this means that all sounds must begin playing from the beginning and cannot be started from or transitioned to an arbitrary timestamp. PyGame’s Music module does support seeking, however, it does not support multiple channel playback, which is a more fundamental drawback.

A workaround for the lack of a seeking feature is to simply sleep the thread until the next audio file chunk should begin. This necessitates that the audio file is broken into a sufficiently large number of chunks to minimize the amount of time of silence -- this was already necessary for supporting remote streaming use-cases as streaming in real time requires a more granular file transfer.

We created an abstraction called “Streamer” that encapsulates notions of streaming an audio channel (locally or remotely) and synchronizing metadata (e.g. timestamp) based on signals from the protocol.

- Local Streamer (extends Streamer)
    - This class captures the core functionality of reading local audio files, interfacing with PyGame Mixer, and synchronizing state from the protocol.
- Remote Stream (does not extend Streamer)
    - This class captures the functionality of serving local audio files to Remote Streamers located on other clients. For our minimal viable product, audio files were not actually served over the network, and were stored locally on every client. However, each remote chunk is marked as “un-downloaded” until it is “downloaded” from the remote stream, where “downloading” is a network request/response with additional simulated latency.
- Remote Streamer (extends Local Streamer)
    - This class captures the functionality of downloading audio files from a Remote Stream in advance of playback, also known as “prefetching”. When a Remote Streamer is created, it will begin downloading chunks from the beginning of the audio channel on a background thread. However, if a Remote Streamer is scheduled to seek / sleep until the next chunk begins, the background thread will begin prefetching at the next chunk once it has finished its current chunk. This prefetching strategy is naive, as it does not consider expected latency in its determination of the next chunk to prefetch.
- All Streamer (extends Streamer)
    - This class captures the functionality of representing the global state of all channels as well as state transitions thereof (e.g. synchronizing timestamps across channels). This enables the UI to display an “ALL” channel screen that displays the average timestamp/volume across all channels, allowing the user to modify across channels.

### User Interface

To build the User Interface (UI) we used the PyGame library. We were disappointed to find that PyGame did not have built in component classes such as a button or a drop-down menu. This limited how pretty our UI looked because all the UI components were built from scratch. That being said, the UI turned out to look pretty nice, all things considered.

The UI was refreshed on a timer that ran on the main thread at a rate that was set by `fps`. Each UI component took a list of streamers. During each refresh, the UI would reflect the properties of the streamer indexed by the channel selected. 

Furthermore, to generalize the UI components, many of the components took lambda
functions as arguments. For example, the volume and seeker slider were initialized from the same `SeekSlider` class. However, the `SeekSlider` class took in a lambda function that returned the value to reflect on the slider, given a streamer. The volume instance of the `SeekSlider` used (lambda s: s.get_volume()), while the seeker instance of `SeekSlider` used (lambda s: s.get_current_time()).

After the UI is manipulated by the user, the UI shows a loading indicator and freezes all actions (except to allow the user to change channels) until `stopLoading()` is called, which indicates that the machines have reached a consensus about what the next state is. While initially `isLoading` was a boolean,`isLoading` would eventually refer to a list of booleans which allowed each channel to be loaded independently of another channel. Meanwhile, the All channel would present a loading indicator if any one of the channels was loading.

### Serialization Over Sockets

There’s only a few types of messages that are sent over the sockets connecting each machine. We’ve opted to create a custom generic wire protocol through the `Model` class. The basic idea is that each `Model` consists of a few fields with specified types. The types determine a (de)serialization of that field’s values to/from `bytes`. An ordering of the fields then determines a (de)serialization of an instance of a `Model` to/from `bytes`.

Our `Model` considers a few primitive data types (`int`, `float`, `bool`, `chr`) as well as `list`s of a constant type. `Model`s may be fields of another `Model`, so there is also some extensibility functionality.

This allows us to determine a few important `Model`s: there is a `ChannelState` for each channel/stem whose fields encapsulate the global state of a given channel. Then `BaseEvent`s denote different user (and thus necessary synchronization) actions (there is `NoneEvent`, `PauseEvent`, `PlayEvent`, `SeekEvent`, and `VolumeEvent`). Right now, each of these events consists of the same data, but we can imagine a scenario where some events might contain other necessary metadata. So when a `BaseEvent` subtype is sent over the wire, an `EventCode` is placed as the first byte of the message to determine how deserialization will be done for the remainder of the message (i.e. these are somewhat dependently typed).

This subtyping scheme also determines our possible `BaseRequests`, which have an `OperationCode` to determine how deserialization is performed. The `BaseRequests` are `HeartbeatRequest` (for synchronization of events and state), `IdentityRequest` (for the startup), and `RemoteStreamRequest` (for the streaming of an audio chunk from a remote machine).

## Future Directions

In our project we were able to sync streamer-state as well as simulate transfer of audio over a network by introducing a random latency between the time that audio is requested and audio is locally `unlocked`. In the future, we would start by actually sending audio packets over the network instead of simulating this behavior. Once implemented, this would allow us to generate audio on our local machines and send this over the network. The implications of this is a conference-call application like Zoom. In this case, audio would be generated from our microphones and then sent over the network. For this case, we would likely switch our audio-socket connection from TCP (used in the case of music streaming) to UDP, which prioritizes packet delivery speeds at the expense of reliability.

We were also interested in exploring the use of MIDI in future projects. By sending MIDI data over the network instead of audio information, we could apply our technology to support “virtual jam sessions”: multiple musicians could play MIDI from different corners of the world in a simulated co-located setting. We could apply additional metadata to the streamer channels, such as the MIDI instrument. Furthermore, we could create cool technologies such as “auto-harmonize”; this would allow novice players to participate in the jam-sessions by transposing their solos to match the chords of more experienced players.

### Debugging Notes

- fun pygame `malloc` error when seeking to a new chunk (!?) [in VSCode terminal only]

- `float` serialization is quite inaccurate at large values! [fixed]

- apparently default arguments in python may be mutable…
that was quite interesting as a source of (de)serialization errors….

### Testing notes

The gist of the tests is to test each of the “primitives” on its own, building up to the choice function. There’s a bit of a neat strategy we can use to get a lot of test cases for these from relatively limited possibilities by permuting the inputs and increasing them (the choice isn’t majority!) and such.
So we can combine test cases across seeks and pauses coming in, and plays and pauses at the same time, and volumes at the same time as all of these. The assumption (and feature) that a user can only perform one event in a heartbeat allows this simple consensus, otherwise we might need more of a ledger to resolve conflicts.

It’s quite hard to write unit tests around the pygame functionality. It is not a particularly “mock” friendly library.

As for integration tests, we are able to create our own “mock” streamer and UI classes to just test message sending locally.
