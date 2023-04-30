# models.py
# in synfony.common

from synfony.common.operations import Opcode
from synfony.common.serialization import SerializationUtils
from synfony.common.util import Model
from typing import Callable, Dict, List

# DATA MODELS

# the basic data model of an `Account`.
Account = Model.model_with_fields(logged_in=bool,
                                  username=str)


# the basic data model of a `Message`.
Message = Model.model_with_fields(delivered=bool,
                                  message=str,
                                  recipient_logged_in=bool,
                                  recipient_username=str,
                                  sender_username=str,
                                  time=int)


# OBJECT MODELS

# these are the basic ones.
class BaseRequest(Model.model_with_fields(opcode=int)):
    """A `Model` which has an `opcode` field, and the ability to peek
        at the `opcode` fields (so we can figure out which deserializers
        to actually use).
    """

    @staticmethod
    def deserialize_opcode(data: bytes) -> int:
        """Deserialize `bytes` to the `int` value of an `Opcode`.
        """
        return SerializationUtils.deserialize_int(data[:1])

    @staticmethod
    def serialize_opcode(val: int) -> bytes:
        """Serialize the `int` value of an `Opcode` to `bytes`.
        """
        return SerializationUtils.serialize_int(val, length=1)

    @staticmethod
    def peek_opcode(data: bytes) -> Opcode:
        """Peek at the first byte of some `bytes` to determine the
            `Opcode`.
        """
        return Opcode(BaseRequest.deserialize_opcode(data[:1]))

    @staticmethod
    def add_fields_with_opcode(opcode: int,
                               field_defaults: Dict[str, object] = {},
                               field_deserializers: Dict[str, Callable] = {},
                               field_serializers: Dict[str, Callable] = {},
                               order_of_fields: List[str] = None,
                               fields_list_nested: Dict[str, type] = {},
                               **new_fields: Dict[str, type]):
        """Creates a new `Model` which also uses an `opcode` field
            (but not the `peek_opcode` functionality, that is unique to
             `BaseRequest`).
        """

        class __impl_class__(
            BaseRequest.add_fields(
                field_defaults=dict(list(field_defaults.items()) +
                                    list(dict(opcode=opcode.value).items())),
                field_deserializers=dict(list(field_deserializers.items()) +
                                         [('opcode',
                                           BaseRequest.deserialize_opcode)]),
                field_serializers=dict(list(field_serializers.items()) +
                                       [('opcode',
                                         BaseRequest.serialize_opcode)]),
                order_of_fields=(order_of_fields or
                                 (['opcode'] +
                                  list(new_fields.keys()))),
                fields_list_nested=fields_list_nested,
                **new_fields)):
            pass

        return __impl_class__


class BaseResponse(BaseRequest.add_fields(error=str)):
    """A `Model` which has an `error` field.
    """

    @staticmethod
    def add_fields_with_opcode(opcode: int,
                               field_defaults: Dict[str, object] = {},
                               field_deserializers: Dict[str, Callable] = {},
                               field_serializers: Dict[str, Callable] = {},
                               order_of_fields: List[str] = None,
                               fields_list_nested: Dict[str, type] = {},
                               **new_fields: Dict[str, type]):
        """Creates a new `Model` which also uses an `error` field.
        """

        class __impl_class__(
            BaseResponse.add_fields(
                field_defaults=dict(list(field_defaults.items()) +
                                    list(dict(opcode=opcode.value).items())),
                field_deserializers=dict(list(field_deserializers.items()) +
                                         [('opcode',
                                           BaseRequest.deserialize_opcode)]),
                field_serializers=dict(list(field_serializers.items()) +
                                       [('opcode',
                                         BaseRequest.serialize_opcode)]),
                order_of_fields=(order_of_fields or
                                 (['opcode'] +
                                  list(new_fields.keys()))),
                fields_list_nested=fields_list_nested,
                **new_fields)):
            pass

        return __impl_class__
