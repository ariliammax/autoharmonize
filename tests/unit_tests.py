# unit_tests.py

from synfony.enums import EventCode, OperationCode
from synfony.models import BaseRequest, HeartbeatRequest, IdentityRequest
from synfony.models import ChannelState, MachineAddress
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
    assert obj.get_field() is None                  # default

    obj.set_field(val)
    assert obj.get_field() == val                   # set works

    obj2 = TestModel(field=val)
    assert obj == obj2                              # eq works

    assert str(obj) == f'field: {val!s}'            # str/repr works


@pytest.mark.parametrize(
    'args',
    [(bool, True),
     (float, 2),
     (int, 3),
     (str, 'a')]
)   # TODO eventually add nested? separate test?
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


# MARK: - `BaseEvent` + `BaseRequest` tests


# MARK: - `ChannelState` tests


pass
