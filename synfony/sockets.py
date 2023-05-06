# sockets.py
# in synfony

from abc import ABC
from socket import AF_INET, SHUT_RDWR, SOCK_STREAM, socket
from synfony.config import Config


class BaseSockets(ABC):
    @classmethod
    def accept(cls, s):
        raise NotImplementedError()

    @classmethod
    def close(cls, s):
        raise NotImplementedError()

    @classmethod
    def recv(cls, connection):
        raise NotImplementedError()

    @classmethod
    def send(cls, connection, data):
        raise NotImplementedError()

    @classmethod
    def sendall(cls, s, data):
        raise NotImplementedError()

    @classmethod
    def shutdown(cls, s):
        raise NotImplementedError()

    @classmethod
    def start_socket(cls,
                     machine_address,
                     timeout=None,
                     bind=False,
                     connect=False):
        raise NotImplementedError()


class TCPSockets(BaseSockets):
    """A class wrapping `socket`, so that we can mock it easily.
    """

    @classmethod
    def accept(cls, s):
        return s.accept()

    @classmethod
    def close(cls, s):
        s.close()

    @classmethod
    def recv(cls, connection):
        return connection.recv(Config.PACKET_MAX_LEN)

    @classmethod
    def send(cls, connection, data):
        raise connection.send(data)

    @classmethod
    def sendall(cls, s, data):
        return s.sendall(data)

    @classmethod
    def shutdown(cls, s):
        s.shutdown(SHUT_RDWR)

    @classmethod
    def start_socket(cls,
                     machine_address,
                     timeout=None,
                     bind=False,
                     connect=False):
        s = socket(AF_INET, SOCK_STREAM)
        s.settimeout(timeout)
        if bind:
            s.bind(
                (machine_address.get_host(),
                 machine_address.get_port())
            )
            s.listen()
        if connect:
            s.connect(
                (machine_address.get_host(),
                 machine_address.get_port())
            )
        return s
