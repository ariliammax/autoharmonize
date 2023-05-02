# util.py
# in synfony

from enum import Enum, EnumMeta
from synfony.serialization import SerializationUtils
from typing import Callable, Dict, List, Optional, Type

import builtins


...


class Interface(object):
    """An abstract `interface` that will be used in e.g. `model_from_proto`
       to autogenerate the sort of useful code we would like.

        attributes:
          `_fields_enum`: An `Enum` subclass which has members of the names
                          of the field name and values of the field type.
    """
    _fields_enum: Optional[type] = None


class Model(object):
    """The abstract "models" created from `interface`s.
       Useful for making new models, or (de)serializing.
    """

    # the fields and their types
    _fields: Dict[str, type] = {}

    # the fields and their defaults (not necessary)
    _field_defaults: Dict[str, object] = {}

    # the fields and their deserializers
    _field_deserializers: Dict[str, Callable] = {}

    # the fields and their serializers
    _field_serializers: Dict[str, Callable] = {}

    # the implicit type within a `list` type field, for deserialization.
    # this makes things ugly in `from_grpc_model` if we had `List[List[..]]`,
    # but we don't so whatever.
    _fields_list_nested: Dict[str, type] = {}

    # the order to (de)serialize fields in.
    _order_of_fields: List[str] = {}

    # TODO: is this necessary? I think not necessarily, but will
    # be at a minimum useful for awkard class attributes sharing object
    # attributes names, so best to just discourage it entirely.
    _reserved_fields = ['fields',
                        'field_defaults'
                        'field_deserializers',
                        'field_serializers',
                        'order_of_fields',
                        'fields_list_nested',
                        'reserved_fields']

    def __eq__(self, other) -> bool:
        """Test for equality on every field's `__eq__`
        """
        return len([n for n in self._fields
                    if getattr(self, f'get_{n!s}', lambda: None)() !=
                    getattr(other, f'get_{n!s}', lambda: None)()]) == 0

    def __str__(self) -> str:
        """Concatenates every field's `__str__`
        """
        return ','.join([f'{n!s}: '
                         f'{getattr(self, f"get_{n!s}", lambda: None)()!s}'
                         for n in self._fields])

    def __repr__(self) -> str:
        """Concatenates every field's `__str__`
        """
        return self.__str__()

    @staticmethod
    def default_deserializer(t: Type) -> Optional[Callable]:
        """The default deserializing function for a type. `None` if not
            explicit.
        """
        match t:
            case builtins.bool:
                return SerializationUtils.deserialize_bool
            case builtins.float:
                return SerializationUtils.deserialize_float
            case builtins.int:
                return SerializationUtils.deserialize_int
            case builtins.str:
                return SerializationUtils.deserialize_str
            case _:
                if t is None:
                    return None
                if issubclass(t, Model):
                    return t.deserialize
                return None

    @staticmethod
    def default_serializer(t: Type) -> Optional[Callable]:
        """The default serializing function for a type. `None` if not
            explicit.
        """
        match t:
            case builtins.bool:
                return SerializationUtils.serialize_bool
            case builtins.float:
                return SerializationUtils.serialize_float
            case builtins.int:
                return SerializationUtils.serialize_int
            case builtins.str:
                return SerializationUtils.serialize_str
            case _:
                if t is None:
                    return None
                if issubclass(t, Model):
                    return lambda x: x.serialize()
                return None

    @staticmethod
    def default_list_deserializer(t: Type) -> Callable:
        """The default list deserializer if we can deduce the items'
            default deserializers (via `default_deserializer`).
        """
        return (lambda d: SerializationUtils.deserialize_list(
                    d,
                    Model.default_deserializer(t),
                    Model.default_serializer(t)))

    @staticmethod
    def default_list_serializer(t: Type) -> Callable:
        """The default list serializer if we can deduce the items'
            default serializers (via `default_serializer`).
        """
        return (lambda v: SerializationUtils.serialize_list(
                    v,
                    Model.default_serializer(t)))

    @classmethod
    def deserialize(cls, data: bytes):
        """Deserialize a `Model` according to its `order_of_fields` and
            `field_deserializers`.

            Can cause some headaches on optional arguments, so assume there
            are no `None` values.
        """
        # TODO: this can get screw-y with optionals.
        # a janky way of doing it without more code would be just doing it
        # on lists (of max len 1).
        obj = cls()
        for name in cls._order_of_fields:
            deserializer = cls._field_deserializers[name]
            serializer = cls._field_serializers[name]

            field_val = deserializer(data)
            length = len(serializer(field_val))

            getattr(obj, f'set_{name!s}', lambda _: obj)(field_val)
            try:
                data = data[length:]
            except Exception:
                break
        return obj

    def serialize(self) -> bytes:
        """Serialize a `Model` according to its `order_of_fields` and
            `field_serializers`.

            Can cause some headaches on optional arguments, so assume there
            are no `None` values.
        """
        return b''.join(self._field_serializers[name](getattr(self,
                                                              f'get_{name!s}',
                                                              lambda:
                                                              None)())
                        for name in self._order_of_fields)

    @classmethod
    def from_grpc_model(model, grpc_obj):
        """Take a `grpcio.Message` subclass instance, and see if we have
            matching fields, and grab them if so. Nothing fancy.
        """
        obj = model()
        for name, t in model._fields.items():
            val = getattr(grpc_obj, name, None)
            if t is list:
                nested_model = model._fields_list_nested.get(name, None)
                if nested_model:
                    val = [nested_model.from_grpc_model(v)
                           for v in val or []]

            getattr(obj, f'set_{name!s}', lambda _: obj)(val)
        return obj

    def as_model(self, model: Type):
        """Create a new `model` instance from this instance, by copying the
            fields we share. Nothing fancy.
        """
        obj = model()
        for name in self._fields:
            getattr(obj, f'set_{name!s}', lambda _: obj)(
                getattr(self, f'get_{name!s}', lambda: None)())
        return obj

    @staticmethod
    def model_with_fields(field_defaults: Dict[str, object] = {},
                          field_deserializers: Dict[str, Callable] = {},
                          field_serializers: Dict[str, Callable] = {},
                          order_of_fields: List[str] = None,
                          fields_list_nested: Dict[str, type] = {},
                          **fields: Dict[str, type]) -> type:
        """Create a new `Model` subclass with the given class attributes.
        """

        for name in fields:
            if name in Model._reserved_fields:
                raise ValueError(f'Field \'{name!s}\' is a reserved name.')

        # this gives the explicit order, or just uses the keys.
        order = order_of_fields or list(fields.keys())

        # set default (de)serializers, if not set
        for name, t in fields.items():
            deserialize = field_deserializers.get(
                name,
                (Model.default_list_deserializer(
                    fields_list_nested.get(name, None))
                 if name in fields_list_nested else None)
                if t is list else
                Model.default_deserializer(t))
            serialize = field_serializers.get(
                name,
                (Model.default_list_serializer(
                    fields_list_nested.get(name, None))
                 if name in fields_list_nested else None)
                if t is list else
                Model.default_serializer(t))

            if serialize is None or deserialize is None:
                raise ValueError(f'Field {name!s} requires a ' +
                                 ('(de)' if deserialize is None
                                  and serialize is None else
                                  'de' if deserialize is None else '') +
                                 'serializer.')

            field_deserializers[name] = deserialize
            field_serializers[name] = serialize

        class __impl_model__(Model):
            # copy is likely safest here...
            _fields = {k: v for k, v in fields.items()}

            _field_defaults = {k: v for k, v in field_defaults.items()}

            _field_deserializers = {k: v
                                    for k, v in field_deserializers.items()}

            _field_serializers = {k: v for k, v in field_serializers.items()}

            _order_of_fields = order

            _fields_list_nested = {k: v for k, v in fields_list_nested.items()}

        return __impl_model__.add_getters_setters()

    @classmethod
    def add_getters_setters(model):
        """Add getters and setters for each field in the model.
        """
        for name, value in model._fields.items():

            if type(value) is not type:
                raise ValueError(f'Field \'{name!s}\' with value '
                                 f'\'{value!r}\' which is not a `type`.')

            # note: you do NOT want to put `private_name` within any of the
            #       implementations that will be `setattr`ed, since then
            #       `private_name` the variable will be bound to the function.
            #       Another way would be to explicitly `del` it, but uh, that's
            #       not very pythonic...
            #
            #       For some stupid, hacky reason the default works.
            #       I guess since it puts it in the function's `__defaults__`
            #       attribute...
            private_name = f'_{name!s}'

            # the getter we'll add to `model`.
            def __impl_setter__(self: model,
                                val: Optional[value],
                                private_name: str = private_name):
                setattr(self, private_name, val)
                return self

            setattr(model, f'set_{name!s}', __impl_setter__)

            # the setter we'll add to `model`.
            def __impl_getter__(self: model,
                                private_name: str = private_name):
                return getattr(self, private_name, None)

            setattr(model, f'get_{name!s}', __impl_getter__)

        # the `__init__` we'll add to `model`.
        # this might get weird with inheritence, but as long as the inherited
        # call `add_getters_setters`, then we should be good.
        def __impl_init__(self, **kwargs) -> model:
            for name in self._fields:
                if name in kwargs:
                    getattr(self, f'set_{name!s}', lambda _: _)(kwargs
                                                                [name])
                else:
                    setattr(self,
                            f'_{name!s}',
                            self._field_defaults.get(name, None))

        setattr(model, '__init__', __impl_init__)

        return model.clean_getters_setters()

    @classmethod
    def clean_getters_setters(model):
        """Remove getters and setters for each field not in the model.
        """
        for attr_name in dir(model):
            match attr_name[:4]:
                case 'get_':
                    if attr_name[4:] not in model._fields:
                        setattr(model, attr_name, None)
                case 'set_':
                    if attr_name[4:] not in model._fields:
                        setattr(model, attr_name, None)
        for name in model._fields:
            if name not in model._order_of_fields:
                model._order_of_fields.append(name)
        return model

    @classmethod
    def add_fields(cls,
                   field_defaults: Dict[str, object] = {},
                   field_deserializers: Dict[str, Callable] = {},
                   field_serializers: Dict[str, Callable] = {},
                   order_of_fields: List[str] = None,
                   fields_list_nested: Dict[str, type] = {},
                   **new_fields: Dict[str, type]) -> type:
        """The same as `model_with_fields`, but using the initial state
            of whatever `Model` subclass it's called from, adding on.
        """
        return Model.model_with_fields(
            field_defaults=dict(list(cls._field_defaults.items()) +
                                list(field_defaults.items())),
            field_deserializers=dict(list(cls._field_deserializers.items()) +
                                     list(field_deserializers.items())),
            field_serializers=dict(list(cls._field_serializers.items()) +
                                   list(field_serializers.items())),
            fields_list_nested=dict(list(cls._fields_list_nested.items()) +
                                    list(fields_list_nested.items())),
            order_of_fields=order_of_fields,
            **dict(list(cls._fields.items()) +
                   list(new_fields.items()))).add_getters_setters()

    @classmethod
    def omit_fields(cls,
                    field_defaults: Dict[str, object] = {},
                    field_deserializers: Dict[str, Callable] = {},
                    field_serializers: Dict[str, Callable] = {},
                    order_of_fields: List[str] = None,
                    fields_list_nested: Dict[str, type] = {},
                    **rm_fields: Dict[str, type]) -> type:
        """The same as `model_with_fields`, but using the initial state
            of whatever `Model` subclass it's called from, removing from.
        """
        for fname in rm_fields:
            if fname not in cls._fields:
                raise ValueError(f'Cannot omit field \'{fname!s}\'; '
                                 f'it is not a field of {cls!s}.')
        return Model.model_with_fields(
            field_defaults=dict(list(cls._field_defaults.items()) +
                                list(field_defaults.items())),
            field_deserializers=dict(list(cls._field_deserializers.items()) +
                                     list(field_deserializers.items())),
            field_serializers=dict(list(cls._field_serializers.items()) +
                                   list(field_serializers.items())),
            order_of_fields=order_of_fields,
            fields_list_nested=dict(list(cls._fields_list_nested.items()) +
                                    list(fields_list_nested.items())),
            **{n: t for n, t in cls._fields.items()
               if n not in rm_fields}).add_getters_setters()


def model_from_proto(iface: type) -> type:
    """Materializes a class with getters and setters from an interface.

        Raises: A `ValueError` if `iface` is not `interface` subclass,
                               if `iface._fields_enum` is not `Enum` subclass
                               if `iface._fields_enum`'s members do not have
                                 `str` names and `type` values.

        Returns: A `class` generated by the `iface : interface`.
    """
    if not issubclass(iface, Interface):
        raise ValueError(f'Arg `iface` ({iface!r}) is not a subclass of '
                         f'`interface` (type is {type(iface)!r}).')

    if not hasattr(iface, '_fields_enum'):
        raise ValueError(f'Arg `iface` ({iface!r}) does not have a '
                         f'`_fields_enum` attribute.')

    not_enum = False
    if (type(iface._fields_enum) is not Enum and
            type(iface._fields_enum) is not EnumMeta):
        not_enum = True

    if not not_enum:
        if (not issubclass(iface._fields_enum, Enum) and
                not issubclass(iface._fields_enum, EnumMeta)):
            not_enum = True

    if not_enum:
        raise ValueError(f'Arg `iface`\'s `_fields_enum` attribute '
                         f'({iface._fields_enum!r}) is not an `Enum` '
                         f'(type is {type(iface._fields_enum)!r}).')

    # we may iterate an `Enum`'s members dictionary by `__members__`.
    return Model.model_from_fields(**dict([(member.name, member.value)
                                           for _, member in
                                           iface._fields_enum.__members__
                                           .items()]))
