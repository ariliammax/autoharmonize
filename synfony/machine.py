# machine.py
# in synfony

from synfony.config import Config
from synfony.enums import EventCode, OperationCode
from synfony.models import BaseRequest, HeartbeatRequest, IdentityRequest
from synfony.models import ChannelState, MachineAddress, NoneEvent
from synfony.sockets import TCPSockets
from synfony.ui import UI
from threading import Thread
from typing import Callable, List


import threading
import time


class Machine:

    _lock = threading.Lock()

    sockets = TCPSockets

    @classmethod
    def startup(cls, idx, machine_addresses, machine_message_queues):
        machine_address = machine_addresses[idx]
        s = cls.sockets.start_socket(
            machine_address=machine_address,
            timeout=None,
            bind=True
        )

        sockets = [None for _ in machine_addresses]

        def connect_to_socket(idx, other_machine_address):
            if other_machine_address.get_idx() == idx:
                with cls._lock:
                    sockets[idx] = s
            else:
                while True:
                    try:
                        other_socket = cls.sockets.start_socket(
                            machine_address=other_machine_address,
                            timeout=Config.HANDSHAKE_TIMEOUT,
                            connect=True
                        )
                        cls.sockets.sendall(
                            other_socket,
                            IdentityRequest(
                                machine_address=machine_address
                            ).serialize()
                        )
                        with cls._lock:
                            sockets[other_machine_address
                                    .get_idx()] = other_socket
                        break
                    except Exception:
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

        return sockets

    @classmethod
    def accept_clients(cls,
                       idx,
                       machine_addresses,
                       s,
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
                connection, _ = cls.sockets.accept(s)

                # 2 - `IdentityRequest`
                request_data = cls.sockets.recv(connection)
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
            except Exception:
                pass

    @classmethod
    def listen_client(cls, idx, connection, machine_message_queues):
        """For continued listening on a client, where the handshakes are
            received.
        """
        while True:
            try:
                request_data = cls.sockets.recv(connection)
                if (BaseRequest.peek_operation_code(request_data) !=
                        OperationCode.HEARTBEAT):
                    continue
                request = HeartbeatRequest.deserialize(request_data)
                with cls._lock:
                    machine_message_queues[idx].append(request)
            except Exception:
                pass

    @classmethod
    def metronome(cls,
                  my_idx: int,
                  sockets,
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

        latest_events = \
            [[event for event in ui_manager.event_queue[::-1]
              if event.get_channel_state().get_idx() == c_idx]
             for c_idx in range(len(ui_manager.streamers))]

        # TODO: lock in UI
        ui_manager.event_queue.clear()
        channel_events_states = \
            [latest_events[c_idx][0]
             # NoneEvent(channel_state=ChannelState(idx=c_idx))
             for c_idx in range(len(ui_manager.streamers))
             if len(latest_events[c_idx]) > 0]
        [event.set_channel_state(
            ChannelState(
                idx=event.get_channel_state().get_idx(),
                last_timestamp=(
                    ui_manager
                    .streamers[event.get_channel_state().get_idx()]
                    .get_last_time()
                ),
                timestamp=(
                    ui_manager
                    .streamers[event.get_channel_state().get_idx()]
                    .get_current_time()
                    if event.get_event_code() != EventCode.SEEK.value else
                    event.get_channel_state().get_timestamp()
                ),
                playing=(
                    ui_manager
                    .streamers[event.get_channel_state().get_idx()]
                    .is_playing()
                ),
                volume=(
                    ui_manager
                    .streamers[event.get_channel_state().get_idx()]
                    .get_volume()
                    if event.get_event_code() != EventCode.VOLUME.value else
                    event.get_channel_state().get_volume()
                )
            )
         ) for event in channel_events_states]

        request = HeartbeatRequest(
            channel_events_states=channel_events_states,
            machine_addresses=machine_addresses,
            sent_timestamp=time.time()
        )
        with cls._lock:
            machine_message_queues[my_idx].append(request)

        request_data = request.serialize()

        # 1 - send to all
        def impl_send_state(s, i: int, request_data: bytes):
            status = False
            while time.time() - start_t < Config.HEARTBEAT_TIMEOUT:
                try:
                    cls.sockets.sendall(s, request_data)
                    status = True
                    break
                except Exception:
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
        [ui_manager.streamers[events[0].get_channel_state().get_idx()].sync(
            choice_func(events)
         )
         for events in all_channel_idx_events
         if len(events) > 0]
        ui_manager.stop_loading()

        # 4 - wait for next
        time.sleep(
            max(Config.HANDSHAKE_INTERVAL - (time.time() - start_t), 0.01)
        )

    @classmethod
    def handler(cls, e, s):
        """Handle any errors that come up.
        """
        try:
            cls.sockets.shutdown(s)
        except Exception:
            pass
        finally:
            cls.sockets.close(s)
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
        sockets = []
        ui_manager = UI()

        def networking(idx: int,
                       machine_addresses: List[MachineAddress],
                       sockets,
                       ui_manager: UI):
            try:
                sockets = cls.startup(
                    idx=idx,
                    machine_addresses=machine_addresses,
                    machine_message_queues=machine_message_queues
                )

                while True:
                    cls.metronome(
                        my_idx=idx,
                        sockets=sockets,
                        machine_addresses=machine_addresses,
                        ui_manager=ui_manager,
                        machine_message_queues=machine_message_queues,
                        choice_func=ChannelState.choice_func
                    )
            except Exception as e:
                cls.handler(e=e, s=sockets[idx])
            finally:
                cls.handler(e=None, s=sockets[idx])

        if Config.HANDSHAKE_ENABLED:
            Thread(target=networking,
                   args=[idx, machine_addresses, sockets, ui_manager]).start()
        ui_manager.init(idx)
