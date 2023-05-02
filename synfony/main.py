# main.py
# in synfony

from argparse import ArgumentParser, Namespace
from multiprocessing import Process
from socket import AF_INET, SHUT_RDWR, SOCK_STREAM, socket
from synfony.config import Config
from synfony.enums import OperationCode
from synfony.models import BaseEvent, \
                           NoneEvent, \
                           PauseEvent, \
                           PlayEvent, \
                           SeekEvent
from synfony.models import BaseRequest, \
                           HeartbeatRequest, \
                           HeartbeatResponse, \
                           IdentityRequest, \
                           IdentityResponse
from synfony.models import ChannelState,  MachineAddress
from synfony.ui import UI
from threading import Thread
from typing import Callable, List, Tuple


import threading
import time


def make_parser():
    """Makes a parser for command line arguments (i.e. machine addresses).
    """
    parser = ArgumentParser()
    parser.add_argument('--idx',
                        required=False,
                        type=int)
    parser.add_argument('--machines',
                        default=Config.MACHINES,
                        required=False,
                        type=list)
    parser.add_argument('--multiprocess',
                        action='store_true',
                        default=False,
                        required=False)
    return parser


def parse_args():
    """Parse the command line arguments (i.e. host and port).

        Returns: an `argparse.Namespace` (filtering out `None` values).
    """
    parser = make_parser()
    return Namespace(**{k: (v if k != 'machines' else [(vv.split(':')[0],
                                                        int(vv.split(':')[1]))
                                                       for vv in v])
                        for k, v in parser.parse_args().__dict__.items()
                        if v is not None})


def accept_clients(machine_addresses, s: socket):
    """Called when the initial handshake between two machines begins.

        The startup protocol is:
            1 - connect
            2 - send `IdentityRequest`s
            3 - start `listen_client` threads
    """
    while True:
        try:
            # 1
            connection, _ = s.accept()

            # 2 - `IdentityRequest`
            request_data = connection.recv(Config.PACKET_MAX_LEN)
            if (BaseRequest.peek_operation_code(request_data) !=
                    OperationCode.IDENTITY):
                continue
            request = IdentityRequest.deserialize(request_data)
            machine_address = request.get_machine_address()
            # TODO lock
            if machine_address.get_idx() >= len(machine_addresses):
                while (machine_address.get_idx() <
                       len(machine_addresses)):
                    machine_addresses.append(None)
            machine_addresses[machine_address.get_idx()] =  machine_address

            # 3 - `listen_client` start
            # TODO: actually do
            print('accepted', s.getsockname())
        except Exception as e:
            pass


def listen_client(idx, connection, machine_message_queues):
    """For continued listening on a client, where the handshakes are received.
    """
    while True:
        # TODO: add to a queue for processing by the handshake event,
        request_data = connection.recv(Config.PACKET_MAX_LEN)
        if (BaseRequest.peek_operation_code(request_data) !=
                OperationCode.HEARTBEAT):
            continue
        request = HeartbeatRequest.deserialize(request_data)
        machine_message_queues.append(request)


def metronome(sockets: List[socket],
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

        (2) can take up to `Config.HEARTBEAT_TIMEOUT` amount of time; so then
        (3, 4) will take up the remainder of time of
            `Config.HANDSHAKE_INTERVAL`, which is a lil longer.

        Also, we are actually doing a bunch of retries in (1) / (2), which
        are timing out in `Config.HANDSHAKE_TIMEOUT`, whcih are much faster
        than `Config.HEARTBEAT_TIMEOUT`.
    """
    start_t = time.time()

    # TODO: locking
    up_machine_addresses=[machine
                          for i, machine in
                          enumerate(machine_addresses)
                          if (machine is not None and
                              machine.get_status())]

    latest_events = \
        [[event for event in ui_manager.event_queue[::-1]
          if event.get_channel_state().get_idx() == idx]
         for idx in range(ui_manager.streamer.get_num_channels())]
    if len(ui_mananger.event_queue) > 0:
        ui_manager.stop_loading()
    ui_manager.event_queue.clear()
    channel_events_states = \
        [latest_events[idx][0] if len(latest_events[idx]) > 0 else NoneEvent()
         for idx in range(ui_manager.streamer.get_num_channels())]
    [event.set_channel_state(
        ChannelState(
            idx=idx,
            timestamp=ui_manager.streamer.get_current_time(idx),
            playing=ui_manager.streamer.is_playing(idx),
            volume=ui_manager.streamer.get_volume(idx)
        )
     ) for idx, event in enumerate(channel_event_states)]

    request = HeartbeatRequest(
        channel_events_states=channel_events_states,
        machine_addresses=machine_addresses,
        sent_timestamp=start_t_ms
    )
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
        # TODO: locking
        machine_addresses[i].set_status(status)

    send_threads = [threading.Thread(target=impl_send_state,
                                     args=[socket[machine.get_idx()],
                                           machine.get_idx(),
                                           request_data])
                    for machine in up_machine_addresses]
    [thread.start() for thread in send_threads]

    # 2 - pull off queue, wait until acceptable
    def message_queues_empty():
        return len(
            [queue for queue, machine in zip(machine_message_queues,
                                             machine_addresses)
             if (len(queue) == 0 and
                 machine is not None and
                 machine.get_status())]
        ) == 0

    while (time.time() - start_t < Config.HEARTBEAT_TIMEOUT and
           message_queues_empty()):
        time.sleep(Config.HANDSHAKE_TIMEOUT)

    [thread.join() for thread in send_threads]

    votes: List[HeartbeatRequest] = []
    for i, queue in enumerate(machine_message_queues):
        machine_addresses[i].set_status(len(queue) != 0 and
                                              machine_addresses[i]
                                              .get_status())
        if len(queue) != 0:
            votes.append(queue[-1])

        machine_message_queues[i].clear()

    # 3 - consensus + `ui_manager.streamer.sync(...)`; and
    #     increment the `._event._timestamp` by
    #     `time.time() - ._sent_timestamp` to account for network latency
    #     (relativistic effects are acceptable and within our
    #     `Config.TOLERABLE_DELAY`)... do this here, since it's the
    #      most accurate we can reasonably get it without going to consensus
    #      (and is likely to be within tolerable range anyways).
    [event.get_channel_state().set_timestamp(
         event.get_channel_state().get_timestamp() +
         time.time() - vote.get_sent_timestamp()
     )
     for vote in votes
     for event in vote.get_channel_events_states()]

    all_channel_idxes = {event.get_channel_state().get_idx()
                         for vote in votes
                         for event in vote.get_channel_events_states()}
    ui_manager.streamer.sync(
        [choice_func([event
                      for vote in votes
                      for event in vote.get_channel_events_states()
                      if event.get_channe_state().get_idx() == channel_idx])
         for channel_idx in all_channel_idxes]
    )

    # 4 - schedule next
    time.sleep(Config.HANDSHAKE_INTERVAL - (time.time() - start_t))
    return metronome(sockets=sockets,
                     machine_addresses=machine_addresses,
                     ui_manager=ui_manager,
                     machine_message_queues=machine_message_queues,
                     choice_func=choice_func)


def handler(e, s: socket):
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


def main(idx: int, machines: List[str]):
    """Start the connections and what not.
    """
    machine_addresses = [MachineAddress(
                             host=machine[0],
                             idx=i,
                             port=machine[1],
                             status=False)
                         for i, machine in enumerate(machines)]
    machine_message_queues = [[] for _ in machines]
    # TODO: pass ui onto `accept_clients`
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

            print('listen', idx)

            sockets = []
            def connect_to_socket(idx, other_machine_address):
                if other_machine_address.get_idx() == idx:
                    sockets.append(s)
                else:
                    while True:
                        try:
                            other_socket = socket(AF_INET, SOCK_STREAM)
                            other_socket.settimeout(Config.HANDSHAKE_TIMEOUT)
                            other_socket.connect(
                                (other_machine_address.get_host(),
                                 other_machine_address.get_port())
                            )
                            other_socket.sendall(
                                IdentityRequest(
                                    machine_address=machine_address
                                ).serialize()
                            )
                            sockets.append(other_socket)
                            break
                        except Exception as e:
                            pass
            connect_threads = [threading.Thread(target=connect_to_socket,
                                                args=[idx,
                                                      other_machine_address])
                               for other_machine_address in machine_addresses]
            [thread.start() for thread in connect_threads]
            threading.Thread(target=accept_clients,
                             args=(machine_addresses, s)).start()
            [thread.join() for thread in connect_threads]

            # if this returns, then we'll close the socket
            # metronome(sockets=sockets,
            #           machine_addresses=machine_addresses,
            #           ui_manager=ui_manager,
            #           machine_message_queues=machine_message_queues,
            #           choice_func=ChannelState.choice_func)
            while True:
                pass
        except Exception as e:
            handler(e=e, s=s)
        finally:
            handler(e=None, s=s)

    Thread(target=networking,
           args=[idx, machine_addresses, ui_manager]).start()
    ui_manager.init(idx)


if __name__ == '__main__':
    args = parse_args()
    if args.multiprocess:
        for idx in range(3):
            p = Process(
                target=main,
                args=(idx, args.machines)
            )
            p.start()
        while True:
            pass
    else:
        main(args.idx, args.machiens)
