# machine.py
# in synfony

from socket import AF_INET, SHUT_RDWR, SOCK_STREAM, socket
from synfony.config import Config
from synfony.enums import EventCode, OperationCode
from synfony.models import BaseEvent, \
                           NoneEvent, \
                           PauseEvent, \
                           PlayEvent, \
                           SeekEvent
from synfony.models import BaseRequest, HeartbeatRequest, IdentityRequest
from synfony.models import ChannelState,  MachineAddress
from synfony.ui import UI
from threading import Thread
from typing import Callable, List, Tuple


import threading
import time


class Machine:

    _lock = threading.Lock()

    @classmethod
    def accept_clients(cls,
                       idx,
                       machine_addresses,
                       s: socket,
                       machine_message_queues):
        """Called when the initial handshake between two machines begins.

            The startup protocol is:
                1 - connect
                2 - send `IdentityRequest`s
                3 - start `listen_client` threads
        """
        while True:
            try:
                # 1 - accept connection
                connection, _ = s.accept()

                # 2 - `IdentityRequest`
                request_data = connection.recv(Config.PACKET_MAX_LEN)
                if (BaseRequest.peek_operation_code(request_data) !=
                        OperationCode.IDENTITY):
                    continue
                request = IdentityRequest.deserialize(request_data)
                machine_address = request.get_machine_address()
                with cls._lock:
                    if machine_address.get_idx() >= len(machine_addresses):
                        while (machine_address.get_idx() <
                               len(machine_addresses)):
                            machine_addresses.append(None)
                    machine_addresses[machine_address.get_idx()] = \
                        machine_address

                # 3 - `listen_client` start
                threading.Thread(
                    target=cls.listen_client,
                    args=[machine_address.get_idx(),
                          connection,
                          machine_message_queues]
                ).start()
            except Exception as e:
                pass


    @classmethod
    def listen_client(cls, idx, connection, machine_message_queues):
        """For continued listening on a client, where the handshakes are
            received.
        """
        while True:
            try:
                request_data = connection.recv(Config.PACKET_MAX_LEN)
                if (BaseRequest.peek_operation_code(request_data) !=
                        OperationCode.HEARTBEAT):
                    continue
                request = HeartbeatRequest.deserialize(request_data)
                with cls._lock:
                    machine_message_queues[idx].append(request)
            except:
                pass


    @classmethod
    def metronome(cls,
                  my_idx: int,
                  sockets: List[socket],
                  machine_addresses: List[MachineAddress],
                  ui_manager: UI,
                  machine_message_queues: List[HeartbeatRequest],
                  choice_func: Callable = ChannelState.choice_func):
        """Share and reach consensus about `state`, so we can pass it to the
            `LocalMusicStreamer`.

            The protocol is:
                1 - send out my state.
                2 - get everyone else's state;
                    if none received, then that guy is down:
                    break the socket so that guy cuts himself out.
                3 - do consensus, update state, call `LocalMusicStreamer.sync`.
                4 - do the next handshake-heartbeat.

            (2) can take up to `Config.HEARTBEAT_TIMEOUT` amount of time; so
            then (3, 4) will take up the remainder of time of
                `Config.HANDSHAKE_INTERVAL`, which is a lil longer.

            Also, we are actually doing a bunch of retries in (1) / (2), which
            are timing out in `Config.HANDSHAKE_TIMEOUT`, whcih are much faster
            than `Config.HEARTBEAT_TIMEOUT`.
        """
        start_t = time.time()

        up_machine_addresses=[machine
                              for i, machine in
                              enumerate(machine_addresses)
                              if (machine is not None and
                                  machine.get_status())]

        latest_events = \
            [[event for event in ui_manager.event_queue[::-1]
              if event.get_channel_state().get_idx() == c_idx]
             for c_idx in range(len(ui_manager.streamers))]

        # TODO: lock in UI
        ui_manager.event_queue.clear()
        channel_events_states = \
            [latest_events[c_idx][0]
             for c_idx in range(len(ui_manager.streamers))
             if len(latest_events[c_idx]) > 0]
        [event.set_channel_state(
            ChannelState(
                idx=
                    c_idx,
                last_timestamp=
                    ui_manager.streamers[c_idx].get_last_time(),
                timestamp=
                    ui_manager.streamers[c_idx].get_current_time()
                    if event.get_event_code() != EventCode.SEEK.value else
                    event.get_channel_state().get_timestamp(),
                playing=
                    ui_manager.streamers[c_idx].is_playing(),
                volume=
                    ui_manager.streamers[c_idx].get_volume()
                    if event.get_event_code() != EventCode.VOLUME.value else
                    event.get_channel_state().get_volume(),
            )
         ) for c_idx, event in enumerate(channel_events_states)]

        request = HeartbeatRequest(
            channel_events_states=channel_events_states,
            machine_addresses=machine_addresses,
            sent_timestamp=time.time()
        )
        with cls._lock:
            machine_message_queues[my_idx].append(request)

        request_data = request.serialize()

        # 1 - send to all
        def impl_send_state(s: socket, i: int, request_data: bytes):
            status = False
            while time.time() - start_t < Config.HEARTBEAT_TIMEOUT:
                try:
                    s.sendall(request_data)
                    status = True
                    break
                except:
                    pass
            with cls._lock:
                machine_addresses[i].set_status(status)

        send_threads = [threading.Thread(target=impl_send_state,
                                         args=[sockets[machine.get_idx()],
                                               machine.get_idx(),
                                               request_data])
                        for machine in machine_addresses
                        if machine is not None and machine.get_idx() != my_idx]
        [thread.start() for thread in send_threads]

        # 2 - pull off queue, wait until acceptable
        def any_message_queues_empty():
            return len(
                [queue for queue in machine_message_queues
                 if len(queue) == 0]
            ) > 0

        while (time.time() - start_t < Config.HEARTBEAT_TIMEOUT and
               any_message_queues_empty()):
            time.sleep(Config.HANDSHAKE_TIMEOUT)

        [thread.join() for thread in send_threads]

        # votes doesn't care about `machine_id`
        votes: List[HeartbeatRequest] = []
        for i, queue in enumerate(machine_message_queues):
            with cls._lock:
                if machine_addresses[i].get_status() and i != my_idx:
                    machine_addresses[i].set_status(len(queue) != 0)

            if len(queue) != 0:
                votes.append(queue[-1])

            with cls._lock:
                machine_message_queues[i].clear()

        # 3 - consensus + `ui_manager.streamer.sync(...)`; and
        #     increment the `._event._timestamp` by
        #     `time.time() - ._sent_timestamp` to account for network latency
        #     (relativistic effects are acceptable and within our
        #     `Config.TOLERABLE_DELAY`)... do this here, since it's the
        #      most accurate we can reasonably get it without going to
        #      consensus (and is likely to be within tolerable range anyways).
        [event.get_channel_state().set_timestamp(
             event.get_channel_state().get_timestamp() +
             max(time.time() - vote.get_sent_timestamp(), 0)
         )
         for vote in votes
         for event in vote.get_channel_events_states()]

        all_channel_idxes = {event.get_channel_state().get_idx()
                             for vote in votes
                             for event in vote.get_channel_events_states()}
        all_channel_idx_events = [
            [event
             for vote in votes
             for event in vote.get_channel_events_states()
             if event.get_channel_state().get_idx() == c_idx]
            for c_idx in all_channel_idxes
        ]
        [ui_manager.streamers[c_idx].sync(
            choice_func(events)
         )
         for c_idx, events in enumerate(all_channel_idx_events)
         if c_idx != len(ui_manager.streamers) - 1 or len(events) == 0]
        ui_manager.stop_loading()

        # 4 - schedule next
        time.sleep(
            max(Config.HANDSHAKE_INTERVAL - (time.time() - start_t), 0.01)
        )
        return cls.metronome(
            my_idx,
            sockets=sockets,
            machine_addresses=machine_addresses,
            ui_manager=ui_manager,
            machine_message_queues=machine_message_queues,
            choice_func=choice_func
        )


    @classmethod
    def handler(cls, e, s: socket):
        """Handle any errors that come up.
        """
        try:
            s.shutdown(SHUT_RDWR)
        except:
            pass
        finally:
            s.close()
        if e is not None:
            raise e


    @classmethod
    def main(cls, idx: int, machines: List[str]):
        """Start the connections and what not.
        """
        machine_addresses = [MachineAddress(
                                 host=machine[0],
                                 idx=i,
                                 port=machine[1],
                                 status=(i == idx))
                             for i, machine in enumerate(machines)]
        machine_message_queues = [[] for _ in machines]
        ui_manager = UI()

        def networking(idx: int,
                       machine_addresses: List[MachineAddress],
                       ui_manager: UI):
            try:
                machine_address = machine_addresses[idx]
                s = socket(AF_INET, SOCK_STREAM)
                s.bind(
                    (machine_address.get_host(),
                     machine_address.get_port())
                )
                s.settimeout(None)  # infinite, so blocking `recv`s
                s.listen()

                sockets = [None for _ in machine_addresses]
                def connect_to_socket(idx, other_machine_address):
                    if other_machine_address.get_idx() == idx:
                        with cls._lock:
                            sockets[idx] = s
                    else:
                        while True:
                            try:
                                other_socket = socket(AF_INET, SOCK_STREAM)
                                other_socket.settimeout(
                                    Config.HANDSHAKE_TIMEOUT
                                )
                                other_socket.connect(
                                    (other_machine_address.get_host(),
                                     other_machine_address.get_port())
                                )
                                other_socket.sendall(
                                    IdentityRequest(
                                        machine_address=machine_address
                                    ).serialize()
                                )
                                with cls._lock:
                                    sockets[other_machine_address
                                            .get_idx()] = other_socket
                                break
                            except Exception as e:
                                pass
                connect_threads = [
                    threading.Thread(
                        target=connect_to_socket,
                        args=[idx, other_machine_address]
                    )
                    for other_machine_address in machine_addresses]
                [thread.start() for thread in connect_threads]
                threading.Thread(
                    target=cls.accept_clients,
                    args=(idx, machine_addresses, s, machine_message_queues)
                ).start()
                [thread.join() for thread in connect_threads]

                time.sleep(Config.TIMEOUT)

                # if this returns, then we'll close the socket
                cls.metronome(
                    my_idx=idx,
                    sockets=sockets,
                    machine_addresses=machine_addresses,
                    ui_manager=ui_manager,
                    machine_message_queues=machine_message_queues,
                    choice_func=ChannelState.choice_func
                )
            except Exception as e:
                cls.handler(e=e, s=s)
            finally:
                cls.handler(e=None, s=s)

        if Config.HANDSHAKE_ENABLED:
            Thread(target=networking,
                   args=[idx, machine_addresses, ui_manager]).start()
        ui_manager.init(idx)
