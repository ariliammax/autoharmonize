# main.py
# in synfony

from argparse import ArgumentParser, Namespace
from multiprocessing import Process
from socket import AF_INET, SOCK_STREAM, socket
from synfony.config import Config
from synfony.ui import initUI
from threading import Thread
from time import sleep
from typing import List, Tuple

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
    """
    for _ in other_machine_addresses:
        connection, _ = s.accept()
        Thread(target=listen_client, args=(connection,)).start()


def listen_client(connection):
    """For continued listening on a client.
    """
    while True:
        _ = connection.recv(Config.INT_LEN)


def handler(e, s: socket):
    """Handle any errors that come up.
    """
    s.close()
    if e is not None:
        raise e


def main(idx: int, machines: List[str]):
    """Start the connections and what not.
    """
    s = socket(AF_INET, SOCK_STREAM)
    try:
        machine_address = machines[idx]
        other_machine_addresses = machines[idx + 1:] + machines[:idx]
        s.bind(machine_address)
        s.listen()
        s.settimeout(None)
        sleep(Config.TIMEOUT)
        Thread(target=accept_clients,
               args=(other_machine_addresses, s)).start()
        sleep(Config.TIMEOUT)
        other_sockets = []
        for other_machine_address in other_machine_addresses:
            other_socket = socket(AF_INET, SOCK_STREAM)
            other_socket.settimeout(None)
            other_socket.connect(other_machine_address)
            other_sockets.append(other_socket)
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
        main(**args.__dict__)
