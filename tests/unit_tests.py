# unit_tests.py

from itertools import permutations
from synfony.enums import EventCode, OperationCode
from synfony.models import BaseRequest, HeartbeatRequest, IdentityRequest
from synfony.models import ChannelState, MachineAddress
from synfony.models import BaseEvent, \
                           NoneEvent, \
                           PauseEvent, \
                           PlayEvent, \
                           SeekEvent, \
                           VolumeEvent
from synfony.util import Model

import pytest


# MARK: - `Model` tests, i.e. deserializations are "good"


@pytest.mark.parametrize(
    'args',
    [(bool, True),
     (float, 2),
     (int, 3),
     (str, 'a')]
)
def test_model_get_set(args):
    t, val = args

    class TestModel(
        Model.model_with_fields(
            field=t
        )
    ):
        pass

    # these are a bunch of sanity checks to make sure that we have the
    # metadata for this field, and no others
    assert TestModel._fields['field'] == t
    assert len(TestModel._field_defaults) == 0
    assert len(TestModel._field_deserializers) == 1
    assert len(TestModel._field_serializers) == 1
    assert len(TestModel._fields_list_nested) == 0
    assert len(TestModel._order_of_fields) == 1

    obj = TestModel()
    assert obj.get_field() is None         # default

    obj.set_field(val)
    assert obj.get_field() == val          # set works

    obj2 = TestModel(field=val)
    assert obj == obj2                     # eq works

    assert repr(obj) == f'field: {val!r}'  # str/repr works


@pytest.mark.parametrize(
    'args',
    [(bool, True),
     (float, 2),
     (int, 3),
     (str, 'a')]
)
def test_model_serialize_deserialize(args):
    t, val = args

    class TestModel(
        Model.model_with_fields(
            field=t
        )
    ):
        pass

    assert TestModel.deserialize(
        TestModel(field=val).serialize()
    ).get_field() == val


@pytest.mark.parametrize(
    'args',
    [(bool, True),
     (float, 2),
     (int, 3),
     (str, 'a')]
)
def test_model_nested(args):
    t, val = args

    class NestedTestModel(
        Model.model_with_fields(
            field=t
        )
    ):
        pass

    class TestModel(
        Model.model_with_fields(
            model=NestedTestModel
        )
    ):
        pass

    obj = TestModel()
    assert obj.get_model() is None                # default

    obj.set_model(NestedTestModel(field=val))
    assert obj.get_model().get_field() == val     # set works

    obj2 = TestModel(model=NestedTestModel(field=val))
    assert obj == obj2                            # eq works

    assert repr(obj) == f'model: field: {val!r}'  # str/repr works

    assert TestModel.deserialize(obj.serialize()) == obj


@pytest.mark.parametrize(
    'args',
    [(bool, True),
     (float, 2),
     (int, 3),
     (str, 'a')]
)
def test_model_list(args):
    t, val = args

    class TestModel(
        Model.model_with_fields(
            field=list,
            fields_list_nested=dict(
                field=t
            )
        )
    ):
        pass

    obj = TestModel()
    assert obj.get_field() is None           # default

    obj.set_field([val])
    assert obj.get_field() == [val]          # set works

    obj2 = TestModel(field=[val])
    assert obj == obj2                       # eq works

    assert repr(obj) == f'field: [{val!r}]'  # str/repr works

    assert TestModel.deserialize(obj.serialize()) == obj


# MARK: - `BaseEvent` tests


# MARK: - `ChannelState` tests


class ChoiceTestCase(
    Model.model_with_fields(
        inputs=list,
        output=ChannelState,
        fields_list_nested=dict(
            inputs=BaseEvent
        )
    )
):
    pass


def new_state(last_timestamp, timestamp, playing, volume):
    return ChannelState(
        idx=0,
        last_timestamp=last_timestamp,
        timestamp=timestamp,
        playing=playing,
        volume=volume,
    )


def new_event(event_code, *state_args):
    match event_code:
        case EventCode.NONE:
            return NoneEvent(channel_state=new_state(*state_args))
        case EventCode.PAUSE:
            return PauseEvent(channel_state=new_state(*state_args))
        case EventCode.PLAY:
            return PlayEvent(channel_state=new_state(*state_args))
        case EventCode.SEEK:
            return SeekEvent(channel_state=new_state(*state_args))
        case EventCode.VOLUME:
            return VolumeEvent(channel_state=new_state(*state_args))


def new_case(inputs, output):
    return ChoiceTestCase(inputs=inputs, output=output)


# TODO: not worth increasing this over 2...
m = 1
UNPERMUTED_CHOICE_TEST_CASES = [
    # NONE EVENTS
    # =============
    # basic stopped. the initial state
    new_case([new_event(EventCode.NONE, 0, 0, False, 0)],
             new_state(0, 0, False, 0)),
    # basic play
    new_case([new_event(EventCode.NONE, 0, 0, False, 0)],
             new_state(0, 0, False, 0)),
    # go forward playing
    # (majority doesn't matter!)
    new_case([new_event(EventCode.NONE, 0, 0, True, 0)] * m +
             [new_event(EventCode.NONE, 0, 1, True, 0)],
             new_state(1, 1, True, 0)),
    # go back to latest last time if a pause
    # (majority doesn't matter!)
    new_case([new_event(EventCode.NONE, 1, 4, False, 0)] +
             [new_event(EventCode.NONE, 1, 1, False, 0)] * m +
             [new_event(EventCode.NONE, 2, 5, False, 0)],
             new_state(2, 2, False, 0)),
    # go back to latest playing if no pause event and someone playing
    new_case([new_event(EventCode.NONE, 1, 4, False, 0)] +
             [new_event(EventCode.NONE, 0, 1, True, 0)] * m +
             [new_event(EventCode.NONE, 2, 5, False, 0)],
             new_state(1, 1, True, 0)),
    # PAUSE EVENTS
    # =============
    # basic stop
    new_case([new_event(EventCode.PAUSE, 3, 4, True, 0)],
             new_state(4, 4, False, 0)),
    # idempotent
    new_case([new_event(EventCode.PAUSE, 4, 4, False, 0)],
             new_state(4, 4, False, 0)),
    # pause applies to furthest (playing) timestamp
    new_case([new_event(EventCode.PAUSE, 3, 4, True, 0)] +
             [new_event(EventCode.NONE, 4, 5, True, 0)] * m +
             [new_event(EventCode.NONE, 4, 6, False, 0)] * m,
             new_state(5, 5, False, 0)),
    # PLAY EVENTS
    # =============
    # basic start
    new_case([new_event(EventCode.PLAY, 4, 4, False, 0)],
             new_state(4, 4, True, 0)),
    # idempotent
    new_case([new_event(EventCode.PLAY, 4, 4, True, 0)],
             new_state(4, 4, True, 0)),
    # play goes to furthest last timestamp
    new_case([new_event(EventCode.PLAY, 4, 4, True, 0)] +
             [new_event(EventCode.NONE, 5, 5, False, 0)] * m +
             [new_event(EventCode.NONE, 6, 6, False, 0)] * m,
             new_state(4, 4, True, 0)),
    # CONFLICTS
    # =============
    # pause will override play
    new_case([new_event(EventCode.PLAY, 4, 4, True, 0)] +
             [new_event(EventCode.PAUSE, 5, 5, True, 0)] * m +
             [new_event(EventCode.NONE, 6, 6, True, 0)] * m,
             new_state(6, 6, False, 0)),
    # pause will override play even if they are paused already!
    new_case([new_event(EventCode.PLAY, 4, 4, False, 0)] +
             [new_event(EventCode.PAUSE, 5, 5, False, 0)] * m +
             [new_event(EventCode.NONE, 6, 6, False, 0)] * m,
             new_state(6, 6, False, 0)),
]


# For seek events, we'll do everything the same as above, but also with
# an added SEEK EVENT which should just override any timestamp adjustments...
# add in reverse so that it doesn't loop infinitely, haha
[UNPERMUTED_CHOICE_TEST_CASES.append(
     new_case(
         case.get_inputs() + [new_event(EventCode.SEEK, 3, 3, False, 0)],
         new_state(3, 3, case.get_output().get_playing(), 0)
     )
 )
 for case in UNPERMUTED_CHOICE_TEST_CASES[::-1]]


# For volume cases, we'll do everything the same as above, but also with
# an added VOLUME EVENT which should do everything the same but just adjust
# volumes... add in reverse so that it doesn't loop infinitely, haha
[UNPERMUTED_CHOICE_TEST_CASES.append(
     new_case(
         case.get_inputs() + [new_event(EventCode.VOLUME, 0, 0, False, 1)],
         new_state(
             case.get_output().get_last_timestamp(),
             case.get_output().get_timestamp(),
             case.get_output().get_playing(),
             1
         )
     )
 )
 for case in UNPERMUTED_CHOICE_TEST_CASES[::-1]]


# TODO: reuse for the actual like communication testing??
ALL_CHOICE_TEST_CASES = [
    ChoiceTestCase(
        inputs=list(permuted_inputs),
        output=test_case.get_output()
    )
    for test_case in UNPERMUTED_CHOICE_TEST_CASES
    for permuted_inputs in permutations(test_case.get_inputs())
]


@pytest.mark.parametrize(
    'test_case',
    ALL_CHOICE_TEST_CASES
)
def test_choice(test_case):
    assert (ChannelState.choice_func(test_case.get_inputs()) ==
            test_case.get_output())


# MARK: - `BaseRequest` tests


# TODO: I'm thinking just the simple peeking + deserialize functionality


# MARK: - `metronome` tests... or do these belong in integration_tests?
pass
