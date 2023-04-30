# main.py
# in synfony.machine

from synfony.common.config import Config
from random import randint
from socket import AF_INET, SOCK_STREAM, socket
from threading import Thread, RLock
from typing import Callable, List, Tuple

import sys
import time


class MessageQueue(object):
    def __init__(self, queue=None):
        self._queue = queue if queue is not None else []
        self._lock = RLock()

    def append(self, item):
        with self._lock:
            self._queue.append(item)

    def __len__(self):
        _len = 0
        with self._lock:
            _len = len(self._queue)
        return _len

    def pop(self, idx):
        item = None
        with self._lock:
            try:
                item = self._queue.pop(0)
            except Exception:
                item = None
        return item


def logical_step(duration_s: float,
                 log,
                 logical_clock_time,
                 message_queue,
                 other_sockets,
                 random_gen):
    start_t_s = time.time()

    event = ""
    if len(message_queue) == 0:
        r = random_gen()

        # 8 since 8*8=64 i.e. long
        data = logical_clock_time.to_bytes(Config.INT_LEN, byteorder='little')

        match r:
            case 1:
                event = Config.MSG_SEND_0
                other_sockets[0].sendall(data)
            case 2:
                event = Config.MSG_SEND_1
                other_sockets[1].sendall(data)
            case 3:
                event = Config.MSG_SEND_01
                other_sockets[0].sendall(data)
                other_sockets[1].sendall(data)
            case _:
                event = Config.MSG_INTERNAL
    else:
        event = Config.MSG_RECV
        logical_clock_time = max(logical_clock_time, message_queue.pop(0))

    remaining_s = -(time.time() - start_t_s)
    while remaining_s < 0:
        # if it is more than a step, make it
        # an integral number of steps
        remaining_s += duration_s
        logical_clock_time += 1

    log.flush()
    log.write(Config.DELIMITER.join([
        f'{event!s}',
        f'{time.time()!s}',
        f'{len(message_queue)!s}',
        f'{logical_clock_time!s}\n']))
    log.flush()
    time.sleep(remaining_s)
    return logical_clock_time


def accept_clients(message_queue, other_machine_addresses, s: socket):
    for _ in other_machine_addresses:
        connection, _ = s.accept()
        Thread(target=listen_client,
               args=(connection, message_queue)).start()


def listen_client(connection, message_queue):
    while True:
        response = connection.recv(Config.INT_LEN)
        logical_clock_time = int.from_bytes(response, byteorder='little')
        message_queue.append(logical_clock_time)


def handler(e, log, s: socket):
    log.close()
    s.close()
    if e is not None:
        raise e


def start(duration_s: float = None,
          handler: Callable = handler,
          log=None,
          machine_address: Tuple = (),
          other_machine_addresses: List[Tuple] = [],
          random_event=Config.RANDOM_EVENT):
    if log is None:
        log = open(
            Config.LOGS +
            machine_address[0] +
            str(machine_address[1]) +
            ".txt",
            "w")
    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.bind(machine_address)
        s.listen()
        s.settimeout(None)
        time.sleep(Config.TIMEOUT)
        message_queue = MessageQueue()
        Thread(target=accept_clients,
               args=(message_queue, other_machine_addresses, s)).start()
        time.sleep(Config.TIMEOUT)
        other_sockets = []
        for other_machine_address in other_machine_addresses:
            other_socket = socket(AF_INET, SOCK_STREAM)
            other_socket.connect(other_machine_address)
            other_sockets.append(other_socket)
        if duration_s is None:
            duration_s = 1 / randint(1, Config.RANDOM_CLOCK)
        main(duration_s=duration_s,
             log=log,
             message_queue=message_queue,
             other_sockets=other_sockets,
             random_event=random_event)
    except Exception as e:
        handler(e=e, log=log, s=s)
    finally:
        handler(e=None, log=log, s=s)


def main(duration_s: float = 1,
         log=sys.__stdout__,
         max_steps: int = None,
         message_queue: MessageQueue = None,
         other_sockets: List = [],
         random_event=Config.RANDOM_EVENT,
         random_gen: Callable = None):
    if random_gen is None:
        def _impl_random_gen():
            return randint(1, random_event)
        random_gen = _impl_random_gen
    logical_clock_time = 0
    steps_taken = 0
    while max_steps is None or steps_taken < max_steps:
        logical_clock_time = (
            logical_step(duration_s=duration_s,
                         log=log,
                         logical_clock_time=logical_clock_time,
                         message_queue=message_queue,
                         other_sockets=other_sockets,
                         random_gen=random_gen)
        )
        steps_taken += 1


if __name__ == "__main__":
    start()
