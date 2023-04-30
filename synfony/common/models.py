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


# Function 0: Log In Account
LogInAccountRequest = BaseRequest.add_fields_with_opcode(
    username=str,
    opcode=Opcode.LOG_IN_ACCOUNT)
LogInAccountResponse = BaseResponse.add_fields_with_opcode(
    opcode=Opcode.LOG_IN_ACCOUNT)

# Function 1: Create Account
CreateAccountRequest = BaseRequest.add_fields_with_opcode(
    username=str,
    opcode=Opcode.CREATE_ACCOUNT)
CreateAccountResponse = BaseResponse.add_fields_with_opcode(
    opcode=Opcode.CREATE_ACCOUNT)


# Function 2: List Accounts
ListAccountsRequest = BaseRequest.add_fields_with_opcode(
    text_wildcard=str,
    opcode=Opcode.LIST_ACCOUNTS)
ListAccountsResponse = BaseResponse.add_fields_with_opcode(
    accounts=list,
    opcode=Opcode.LIST_ACCOUNTS,
    fields_list_nested=dict(
        accounts=Account))


# Function 3: Send Message
SendMessageRequest = BaseRequest.add_fields_with_opcode(
    message=str,
    recipient_username=str,
    sender_username=str,
    opcode=Opcode.SEND_MESSAGE)
SendMessageResponse = BaseResponse.add_fields_with_opcode(
    opcode=Opcode.SEND_MESSAGE)


# Function 4: Deliver Undelivered Messages
DeliverUndeliveredMessagesRequest = BaseRequest.add_fields_with_opcode(
    logged_in=bool,
    username=str,
    opcode=Opcode.DELIVER_UNDELIVERED_MESSAGES)
DeliverUndeliveredMessagesResponse = BaseResponse.add_fields_with_opcode(
    messages=list,
    opcode=Opcode.DELIVER_UNDELIVERED_MESSAGES,
    fields_list_nested=dict(
        messages=Message))


# Function 4.1: Acknowledge Messages
AcknowledgeMessagesRequest = BaseRequest.add_fields_with_opcode(
    messages=list,
    opcode=Opcode.ACKNOWLEDGE_MESSAGES,
    fields_list_nested=dict(
        messages=Message))
AcknowledgeMessagesResponse = BaseResponse.add_fields_with_opcode(
    opcode=Opcode.ACKNOWLEDGE_MESSAGES)


# Function 5: Delete Account
DeleteAccountRequest = BaseRequest.add_fields_with_opcode(
    username=str,
    opcode=Opcode.DELETE_ACCOUNT)
DeleteAccountResponse = BaseResponse.add_fields_with_opcode(
    opcode=Opcode.DELETE_ACCOUNT)


# Function 6: Log Out Account
LogOutAccountRequest = BaseRequest.add_fields_with_opcode(
    username=str,
    opcode=Opcode.LOG_OUT_ACCOUNT)
LogOutAccountResponse = BaseResponse.add_fields_with_opcode(
    opcode=Opcode.LOG_OUT_ACCOUNT)
