# main.py
# in synfony

from argparse import ArgumentParser, Namespace
from multiprocessing import Process
from socket import AF_INET, SHUT_RDWR, SOCK_STREAM, socket
from synfony.config import Config
from synfony.enums import EventCode, OperationCode
from synfony.models import BaseEvent, PauseEvent, PlayEvent, SeekEvent
from synfony.models import ChannelState, consensus
from synfony.models import MachineAddress
from synfony.models import IdentityRequest, IdentityResponse
from synfony.models import HeartbeatRequest, HeartbeatResponse
from synfony.ui import initUI
from typing import List, Tuple


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


def accept_clients(other_machine_addresses, s: socket):
    """Called when the initial handshake between two machines begins.

        The startup protocol is:
            1 - connect
            2 - send `IdentityRequest`s
    """
    while True:
        # 1
        connection, _ = s.accept()
        continue

        # 2 - `IdentityRequest`
        while True:
            try:
                request_data = connection.recv(Config.PACKET_MAX_LEN)
                if (IdentityRequest.peek_event_code(request_data) !=
                        EventCode.IdentityRequest):
                    continue
                request = IdentityRequest.deserialize(request_data)
                machine_address = request.get_machine_address()
                # TODO lock
                if machine_address.get_idx() >= len(other_machine_addresses):
                    while (machine_address.get_idx() <
                           len(other_machine_addresses)):
                        other_machines_addresses.append(None)
                other_machine_addresses[machine_address.get_idx()] = \
                    machine_address
                # TODO: join that new address...maybe send it over that
                # socket instead...
                # TODO: update timeout times for handshaking
                break
            except:
                pass


def listen_client(idx, connection):
    """For continued listening on a client, where the handshakes are received.
    """
    while True:
        # TODO: add to a queue for processing by the handshake event
        _ = connection.recv(Config.PACKET_MAX_LEN)


def metronome(other_sockets: List[socket],
              state: ChannelState,
              events: List[BaseEvent]):
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
    start_t_ms = int(1000 * start_t)

    # TODO: locking
    machine_addresses=[machine
                       for i, machine in
                       enumerate(other_machine_addresses)
                       if (machine is not None and
                           machine.get_status())]

    # TODO: get from UI when it is exposed
    #       something like `ui_manager.streamer.yada`
    channel_state = ChannelState(
        idx=0,
        timestamp=0,
        playing=False,
        volume=0
    )

    # TODO: get events from UI when it is exposed, and deduce which is the
    #       most recent etc.
    event = PauseEvent(
        channel_state=channel_state,
        realtime=0
    )

    request = HeartbeatRequest(
        channel_events_states=[event],
        machine_addresses=machine_addresses,
        sent_timestamp=start_t_ms
    )
    request_b = request.serialize()

    # 1 - send to all
    def impl_send_state(s: socket, i: int, request_b: bytes):
        status = False
        while time.time() - start_t < Config.HEARTBEAT_TIMEOUT:
            try:
                s.sendall(request_b)
                status = True
                break
            except:
                pass
        # TODO: lock
        other_machine_addresses[i].set_status(status)
    # TODO: start threads

    # 2 - pull off queue, wait until acceptable
    def message_queues_empty():
        return False

    while (time.time() - start_t < Config.HEARTBEAT_TIMEOUT and
           message_queues_empty()):
        time.sleep(Config.HANDSHAKE_TIMEOUT)

    # TODO: join threads from before

    votes: List[HeartbeatRequest] = []
    for i, queue in enumerate(machine_message_queues):
        other_machine_addresses[i].set_status(len(queue) != 0 and
                                              other_machine_addresses[i]
                                              .get_status())
        if len(queue) != 0:
            votes.append(queue[-1])

        machine_message_queues[i].clear()

    # 3 - consensus + `ui_manager.streamer.sync(...)`
    all_channel_idxes = {event.get_channel_state().get_idx()
                         for vote in votes
                         for event in vote.get_channel_events_states()}

    # TODO: update channel states in `ui_manager`
    for channel_idx in all_channel_idxes:
        new_channel_state = consensus([event
                                       for vote in votes
                                       for event in
                                       vote.get_channel_events_states()
                                       if (event.get_channe_state()
                                           .get_idx() == channel_idx)])
    # TODO: call `ui.manager.streamer.sync(...)`

    # 4 - schedule next
    # TODO: correct arguments...
    timer = threading.Timer(interval=(Config.HANDSHAKE_INTERVAL - start_t),
                            function=handshake)
    timer.start()


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
    # machine_addresses = [MachineAddress(
    #                          host=machine[0],
    #                          idx=-1,
    #                          port=machine[1],
    #                          status=False)]
    s = socket(AF_INET, SOCK_STREAM)
    try:
        machine_address = machines[idx]
        other_machine_addresses = machines[idx + 1:] + machines[:idx]
        s.bind(machine_address)
        s.listen()
        s.settimeout(None)
        # this should be `machine_addresses: List[MachineAddress]`
        threading.Thread(target=accept_clients,
                         args=(other_machine_addresses, s)).start()
        # TODO: start timer for handshake
        other_sockets = []
        for other_machine_address in other_machine_addresses:
            while True:
                try:
                    other_socket = socket(AF_INET, SOCK_STREAM)
                    # TODO handshake timeout post start
                    other_socket.settimeout(None)
                    other_socket.connect(other_machine_address)
                    # other_socket.sendall(IdentityRequest(
                    #     idx=idx,
                    #     machine_address=machine_address).serialize()
                    # )
                    other_sockets.append(other_socket)
                    break
                except:
                    continue
        initUI()
    except Exception as e:
        handler(e=e, s=s)
    finally:
        handler(e=None, s=s)


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
