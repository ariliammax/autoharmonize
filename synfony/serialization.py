# serialization.py
# in synfony

from math import log
from synfony.config import Config
from typing import Callable, Optional

import struct


# this is supposed to be ceiling(log_2(...) / 8), but too lazy to calculate
# that.
# the reason for that function:
# `int.to_bytes(length=num_chars, byteorder='little')` uses ASCII
# to encode the `int`, which is 256, i.e. 2 ** 8, i.e. log_2 / 8, to find the
# number of `char`s.
# anyways, this isn't exactly that, but a safe over-approximation.

# the number of bits taken up in serializing an `int` using `chr`s
FLOAT_LEN_BYTES = 4
# the number of bits taken up in serializing an `int` using `chr`s
INT_LEN_BYTES = int(log(Config.INT_MAX_LEN) / 8) + 1
# the number of bits taken up in serializing an `int` encoding a `list`'s `len`
LIST_LEN_BYTES = int(log(Config.LIST_MAX_LEN) / 8) + 1
# the number of bits taken up in serializing an `int` encoding a `str`'s `len`
STR_LEN_BYTES = int(log(Config.STR_MAX_LEN) / 8) + 1


class SerializationUtils:
    """A bunch of helpers for serialization of standard types.
    """

    @staticmethod
    def deserialize_bool(data: bytes) -> bool:
        """Deserialize a `bool` encoded in a `bytes`.
            It will be length 1.
        """
        return bool.from_bytes(data[:1], byteorder='little')

    @staticmethod
    def serialize_bool(val: bool) -> bytes:
        """Serialize a `bool` into a `bytes`.
            It will be length 1.
        """
        return bool(val).to_bytes(1, byteorder='little')

    @staticmethod
    def deserialize_float(data: bytes) -> float:
        """Deserialize `bytes` into an `float`.
        """
        return struct.unpack('f', data[:min(FLOAT_LEN_BYTES, len(data))])[0]

    @staticmethod
    def serialize_float(val: float) -> bytes:
        """Serialize an `float` into a `bytes`.
        """
        return struct.pack('f', float(val))

    @staticmethod
    def deserialize_int(data: bytes, length: int = INT_LEN_BYTES) -> int:
        """Deserialize `bytes` into an `int`.
            It will be length `length`.
        """
        return int.from_bytes(data[:min(length, len(data))],
                              byteorder='little')

    @staticmethod
    def serialize_int(val: int, length: int = INT_LEN_BYTES) -> bytes:
        """Serialize an `int` into a `bytes`.
            It will be length `length`.
        """
        return int(val).to_bytes(length, byteorder='little')

    @staticmethod
    def deserialize_str(data: bytes) -> str:
        """Deserialize `bytes` into a `str`.
        """
        length = SerializationUtils.deserialize_int(data[:STR_LEN_BYTES],
                                                    length=STR_LEN_BYTES)
        return data[STR_LEN_BYTES:length + STR_LEN_BYTES].decode('utf-8')

    @staticmethod
    def serialize_str(val: str) -> bytes:
        """Serialize a `str` into a `bytes`.
            It uses a 'utf-8' encoding, then the first few `bytes` are
            the length of that encoding, followed by the encoding.
        """
        encoded = (str(val or '').encode('utf-8'))[:Config.STR_MAX_LEN]
        return SerializationUtils.serialize_int(
            len(encoded),
            length=STR_LEN_BYTES) + encoded

    @staticmethod
    def deserialize_list(data: bytes,
                         item_deserialize: Callable,
                         item_serialize: Callable,
                         remain: Optional[int] = None) -> bytes:
        """Deserialize `bytes` into a `list` using some explicit item
            (de)serialization. First few `bytes` are the length of the `list`,
            then we use `item_deserialize` to get each item, figure out how
            far to seek ahead using `len(item_serialize(...))` on the
            deserialized object.
        """
        if remain is None:
            length = SerializationUtils.deserialize_int(data[:LIST_LEN_BYTES],
                                                        length=LIST_LEN_BYTES)
            return SerializationUtils.deserialize_list(data[LIST_LEN_BYTES:],
                                                       item_deserialize,
                                                       item_serialize,
                                                       remain=length)
        elif remain == 0:
            return []
        else:
            obj = item_deserialize(data)
            length = len(item_serialize(obj))
            return [obj] + SerializationUtils.deserialize_list(
                data[length:],
                item_deserialize,
                item_serialize,
                remain=remain - 1)

    @staticmethod
    def serialize_list(val: list,
                       item_serialize: Callable,
                       remain: Optional[int] = None) -> bytes:
        """Serialize `list` into `bytes` using some explicit item
            serialization. First few `bytes` are the length of the `list`,
            then we use `item_serialize` for each item and concat the results.
        """
        if val is None:
            val = []
        if remain is None:
            val = val[:Config.LIST_MAX_LEN]
            return (SerializationUtils.serialize_int(len(val),
                                                     length=LIST_LEN_BYTES) +
                    SerializationUtils.serialize_list(val,
                                                      item_serialize,
                                                      remain=len(val)))
        elif remain == 0:
            return b''
        else:
            return (item_serialize(val[0]) +
                    SerializationUtils.serialize_list(val[1:],
                                                      item_serialize,
                                                      remain=remain - 1))
