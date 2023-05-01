# models.py
# in synfony

from synfony.enums import OperationCode, EventCode
from synfony.serialization import SerializationUtils
from synfony.util import Model
from typing import Callable, Dict, List


# DATA MODELS


MachineAddress = Model.model_with_fields(
    host=str,
    idx=int,
    port=int,
    status=bool
)


class BaseEvent(Model.model_with_fields(event_code=int)):
    """the basic data model of the `Event`s. Like operations, we will have to
        "peek" at the event code to see how to properly deserialize.
    """

    @staticmethod
    def deserialize_event_code(data: bytes) -> int:
        """Deserialize `bytes` to the `int` value of an `EventCode`.
        """
        return SerializationUtils.deserialize_int(data[:1])

    @staticmethod
    def serialize_event_code(val: int) -> bytes:
        """Serialize the `int` value of an `EventCode` to `bytes`.
        """
        return SerializationUtils.serialize_int(val, length=1)

    @staticmethod
    def peek_event_code(data: bytes) -> EventCode:
        """Peek at the first byte of some `bytes` to determine the
            `EventCode`.
        """
        return EventCode(BaseRequest.deserialize_event_code(data[:1]))

    @classmethod
    def deserialize(cls, data: bytes):
        """Deserialize a `BaseEvent` based on its `event_code`.
        """
        event_code = EventCode(BaseEvent.peek_event_code(data))
        match event_code:
            case EventCode.NONE:
                return super(BaseEvent, NoneEvent).deserialize(data)
            case EventCode.PAUSE:
                return super(BaseEvent, PauseEvent).deserialize(data)
            case EventCode.PLAY:
                return super(BaseEvent, PlayEvent).deserialize(data)
            case EventCode.SEEK:
                return super(BaseEvent, SeekEvent).deserialize(data)
            case EventCode.VOLUME:
                return super(BaseEvent, VolumeEvent).deserialize(data)
            case _:
                raise NotImplementedError()

    @staticmethod
    def add_fields_with_event_code(
            event_code: int,
            field_defaults: Dict[str, object] = {},
            field_deserializers: Dict[str, Callable] = {},
            field_serializers: Dict[str, Callable] = {},
            order_of_fields: List[str] = None,
            fields_list_nested: Dict[str, type] = {},
            **new_fields: Dict[str, type]):
        """Creates a new `Model` which also uses an `event_code` field
            (but not the `peek_event_code` functionality, that is unique to
             `BaseRequest`).
        """

        class __impl_class__(
            BaseEvent.add_fields(
                field_defaults=dict(list(field_defaults.items()) +
                                    list(dict(event_code=
                                              event_code.value)
                                         .items())),
                field_deserializers=dict(list(field_deserializers.items()) +
                                         [('event_code',
                                           BaseEvent
                                           .deserialize_event_code)]),
                field_serializers=dict(list(field_serializers.items()) +
                                       [('event_code',
                                         BaseEvent
                                         .serialize_event_code)]),
                order_of_fields=(order_of_fields or
                                 (['event_code'] +
                                  list(new_fields.keys()))),
                fields_list_nested=fields_list_nested,
                **new_fields)):
            pass

        return __impl_class__


class ChannelState(Model.model_with_fields(
                           idx=int,
                           timestamp=int,
                           playing=bool,
                           # TODO: loading / buffering?
                           volume=int
                       )
                   ):
    """this is the state which must reach consensus.
        we don't do so through a strict equality, but rather there is a
        deterministic choice function from a bunch of states.
    """

    @staticmethod
    def choice_func(channel_idx: int, channel_events_states: List[BaseEvent]):
        """Reach consensus of what the global channel states are,
            from each of the machine states from sent.

            Roughly, the protocol is:
                1 - time which is latest is inherited in the updated state
                    there is an important exception: if the further time along
                    is from a not playing and there are playing, then ignore.
                    Otherwise, seeks will cascade from not playing scheduled.

                2 - pausing takes precedence over playing over seeking

                3 - conflicting seeks go to the furthest along
        """
        if len(channel_events_states) == 0:
            return DEFAULT_CHANNEL_STATE

        ordered_states = [state for state in channel_events_states]
        ordered_states.sort(key=lambda state: -1 * state.get_timestamp())

        any_pause = len([state for state in ordered_states
                         if state.get_event_code() == EventCode.PAUSE.value]) > 0

        any_play = len([state for state in ordered_states
                        if state.get_event_code() == EventCode.PLAY.value]) > 0

        any_playing = len([state for state in ordered_states
                           if state.get_playing()]) > 0

        seek_idxes = [i for i, state in enumerate(ordered_states)
                      if state.get_event_code() == EventCode.SEEK.value]
        any_seek = len(seek_idxes) > 0
        if not any_seek and not any_playing:
            seek_idxes = [0]
        if not any_seek:
            seek_idxes = [i for i, state in enumerate(ordered_states)
                          if state.get_playing()]

        vol_idxes = [i for i, state in enumerate(ordered_states)
                     if state.get_event_code() == EventCode.VOLUME.value]
        any_vol = len(vol_idxes) > 0
        if not any_vol:
            vol_idxes = [0]

        return ChannelState(
            idx=channel_idx,
            timestamp=ordered_states[seek_idxes[0]].get_timestamp(),
            playing=(False if any_pause else (any_play or any_playing)),
            volume=ordered_states[vol_idxes[0]].get_volume()
        )

DEFAULT_CHANNEL_STATE = ChannelState(
    idx=0,
    timestamp=0,
    playing=False,
    volume=100
)


# there is a global consensus of the channel "state", but that may be
# slightly modified on each machine (i.e. through mixing)
MixedChannelState = ChannelState.add_fields(
    muted=bool,
)


NoneEvent = BaseEvent.add_fields_with_event_code(
    channel_state=ChannelState,
    event_code=EventCode.NONE
)

PauseEvent = BaseEvent.add_fields_with_event_code(
    channel_state=ChannelState,
    event_code=EventCode.PAUSE
)


PlayEvent = BaseEvent.add_fields_with_event_code(
    channel_state=ChannelState,
    # realtime=int, TODO?
    event_code=EventCode.PLAY
)


SeekEvent = BaseEvent.add_fields_with_event_code(
    channel_state=ChannelState,
    # realtime=int, TODO ?
    event_code=EventCode.SEEK
)


VolumeEvent = BaseEvent.add_fields_with_event_code(
    channel_state=ChannelState,
    event_code=EventCode.VOLUME
)


# OBJECT MODELS

# these are the basic ones.
class BaseRequest(Model.model_with_fields(operation_code=int)):
    """A `Model` which has an `operation_code` field, and the ability to peek
        at the `operation_code` fields (so we can figure out which
        deserializers to actually use).
    """

    @staticmethod
    def deserialize_operation_code(data: bytes) -> int:
        """Deserialize `bytes` to the `int` value of an `OperationCode`.
        """
        return SerializationUtils.deserialize_int(data[:1])

    @staticmethod
    def serialize_operation_code(val: int) -> bytes:
        """Serialize the `int` value of an `OperationCode` to `bytes`.
        """
        return SerializationUtils.serialize_int(val, length=1)

    @staticmethod
    def peek_operation_code(data: bytes) -> OperationCode:
        """Peek at the first byte of some `bytes` to determine the
            `OperationCode`.
        """
        return OperationCode(BaseRequest.deserialize_operation_code(data[:1]))

    @classmethod
    def deserialize(cls, data: bytes):
        """Deserialize a `BaseRequest` based on its `operation_code`.
        """
        operation_code = OperationCode(BaseRequest.peek_operation_code(data))
        match operation_code:
            case OperationCode.HEARTBEAT:
                return super(BaseResponse, HeartbeatRequest).deserialize(data)
            case _:
                raise NotImplementedError()

    @staticmethod
    def add_fields_with_operation_code(
            operation_code: int,
            field_defaults: Dict[str, object] = {},
            field_deserializers: Dict[str, Callable] = {},
            field_serializers: Dict[str, Callable] = {},
            order_of_fields: List[str] = None,
            fields_list_nested: Dict[str, type] = {},
            **new_fields: Dict[str, type]):
        """Creates a new `Model` which also uses an `operation_code` field
            (but not the `peek_operation_code` functionality, that is unique to
             `BaseRequest`).
        """

        class __impl_class__(
            BaseRequest.add_fields(
                field_defaults=dict(list(field_defaults.items()) +
                                    list(dict(operation_code=
                                              operation_code.value)
                                         .items())),
                field_deserializers=dict(list(field_deserializers.items()) +
                                         [('operation_code',
                                           BaseRequest
                                           .deserialize_operation_code)]),
                field_serializers=dict(list(field_serializers.items()) +
                                       [('operation_code',
                                         BaseRequest
                                         .serialize_operation_code)]),
                order_of_fields=(order_of_fields or
                                 (['operation_code'] +
                                  list(new_fields.keys()))),
                fields_list_nested=fields_list_nested,
                **new_fields)):
            pass

        return __impl_class__


class BaseResponse(BaseRequest.add_fields(error=str)):
    """A `Model` which has an `error` field.
    """

    @staticmethod
    def deserialize_operation_code(data: bytes) -> int:
        """Deserialize `bytes` to the `int` value of an `OperationCode`.
        """
        return SerializationUtils.deserialize_int(data[:1])

    @staticmethod
    def serialize_operation_code(val: int) -> bytes:
        """Serialize the `int` value of an `OperationCode` to `bytes`.
        """
        return SerializationUtils.serialize_int(val, length=1)

    @staticmethod
    def peek_operation_code(data: bytes) -> OperationCode:
        """Peek at the first byte of some `bytes` to determine the
            `OperationCode`.
        """
        return OperationCode(BaseResponse.deserialize_operation_code(data[:1]))

    @classmethod
    def deserialize(cls, data: bytes):
        """Deserialize a `BaseRequest` based on its `operation_code`.
        """
        operation_code = OperationCode(BaseResponse.peek_operation_code(data))
        match operation_code:
            case OperationCode.HEARTBEAT:
                return super(BaseResponse, HeartbeatResponse).deserialize(data)
            case _:
                raise NotImplementedError()

    @staticmethod
    def add_fields_with_operation_code(
            operation_code: int,
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
                                    list(dict(operation_code=
                                              operation_code.value)
                                         .items())),
                field_deserializers=dict(list(field_deserializers.items()) +
                                         [('operation_code',
                                           BaseResponse
                                           .deserialize_operation_code)]),
                field_serializers=dict(list(field_serializers.items()) +
                                       [('operation_code',
                                         BaseResponse
                                         .serialize_operation_code)]),
                order_of_fields=(order_of_fields or
                                 (['operation_code'] +
                                  list(new_fields.keys()))),
                fields_list_nested=fields_list_nested,
                **new_fields)):
            pass

        return __impl_class__


HeartbeatRequest = BaseRequest.add_fields_with_operation_code(
    channel_events_states=list,
    machine_addresses=list,
    sent_timestamp=int,
    operation_code=OperationCode.HEARTBEAT,
    fields_list_nested=dict(
        channel_events_states=BaseEvent,
        machine_addresses=MachineAddress
    )
)
HeartbeatResponse = BaseResponse.add_fields_with_operation_code(
    operation_code=OperationCode.HEARTBEAT
)


IdentityRequest = BaseRequest.add_fields_with_operation_code(
    idx=int,
    machine_address=MachineAddress,
    operation_code=OperationCode.IDENTITY
)
IdentityResponse = BaseResponse.add_fields_with_operation_code(
    operation_code=OperationCode.IDENTITY,
)
