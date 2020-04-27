import json
import types

import pytest

from faktory.utilities import collections
from faktory.utilities.collections import DotDict, as_nested_dict, merge_dicts


@pytest.fixture
def nested_dict():
    return {1: 2, 2: {1: 2, 3: 4}, 3: {1: 2, 3: {4: 5, 6: {7: 8}}}}


@pytest.fixture(params=[dict(another=500), DotDict(another=500)])
def mutable_mapping(request):
    "MutableMapping objects to test with"
    return request.param


class TestDotDict:
    def test_initialization_with_kwargs(self):
        d = DotDict(car=10, attr="string", other=lambda x: {})
        assert "another" not in d
        assert "car" in d
        assert "attr" in d
        assert "other" in d

    def test_initialization_with_mutable_mapping(self, mutable_mapping):
        d = DotDict(mutable_mapping)
        assert "car" not in d
        assert "another" in d

    def test_update_with_kwargs(self):
        d = DotDict(car=10, attr="string", other=lambda x: {})
        assert "another" not in d
        d.update(another=500)
        assert "another" in d
        assert d["another"] == 500

    def test_update_with_mutable_mapping(self, mutable_mapping):
        d = DotDict({"car": 10, "attr": "string", "other": lambda x: {}})
        assert "another" not in d
        d.update(mutable_mapping)
        assert "another" in d

    def test_len(self):
        d = DotDict({"car": 10, "attr": "string", "other": lambda x: {}})
        assert len(d) == 3
        a = DotDict()
        assert len(a) == 0
        a.update(new=4)
        assert len(a) == 1
        del d["car"]
        assert len(d) == 2

    def test_attr_updates_and_key_updates_agree(self):
        d = DotDict(data=5)
        d.data += 1
        assert d["data"] == 6
        d["new"] = "value"
        assert d.new == "value"
        d.another_key = "another_value"
        assert d["another_key"] == "another_value"

    def test_del_with_getitem(self):
        d = DotDict(data=5)
        del d["data"]
        assert "data" not in d
        assert len(d) == 0

    def test_del_with_attr(self):
        d = DotDict(data=5)
        del d.data
        assert "data" not in d
        assert len(d) == 0

    def test_get(self):
        d = DotDict(data=5)
        assert d.get("data") == 5
        assert d.get("no_data") is None
        assert d.get("no_data", "fallback") == "fallback"

    def test_setitem(self):
        d = DotDict()
        d["a"] = 1
        assert d["a"] == 1
        d["a"] = 2
        assert d["a"] == 2

    def test_setitem_nonstring_key(self):
        d = DotDict()
        d[1] = 1
        assert d[1] == 1
        d[1] = 2
        assert d[1] == 2

    def test_initialize_from_nonstring_keys(self):
        d = DotDict({1: 1, "a": 2})
        assert d[1] == 1 and d["a"] == 2

    def test_repr_sorts_mixed_keys(self):
        d = DotDict()
        assert repr(d) == "<DotDict>"
        d["a"] = 1
        d[1] = 1
        d["b"] = 1
        assert repr(d) == "<DotDict: 'a', 'b', 1>"

    def test_copy(self):
        d = DotDict(a=1, b=2, c=3)
        assert d == d.copy()

    def test_eq_empty(self):
        assert DotDict() == DotDict()

    def test_eq_empty_dict(self):
        assert DotDict() == {}

    def test_eq_complex(self):
        x = dict(x=1, y=dict(z=[3, 4, dict(a=5)]))
        assert as_nested_dict(x) == as_nested_dict(x)

    def test_eq_complex_dict(self):
        x = dict(x=1, y=dict(z=[3, 4, dict(a=5)]))
        assert as_nested_dict(x) == x

    def test_keyerror_is_thrown_when_accessing_nonexistent_key(self):
        d = DotDict(data=5)
        with pytest.raises(KeyError):
            d["nothing"]

    def test_attributeerror_is_thrown_when_accessing_nonexistent_attr(self):
        d = DotDict(data=5)
        with pytest.raises(AttributeError):
            d.nothing

    def test_iter(self):
        d = DotDict(data=5, car="best")
        res = set()
        for item in d:
            res.add(item)
        assert res == {"data", "car"}

    def test_setdefault_works(self):
        d = DotDict(car="best")
        d.setdefault("data", 5)
        assert d["data"] == 5
        assert d["car"] == "best"

    def test_items(self):
        d = DotDict(data=5, car="best")
        res = set()
        for k, v in d.items():
            res.add((k, v))
        assert res == {("data", 5), ("car", "best")}

    def test_clear_clears_keys_and_attrs(self):
        d = DotDict(data=5, car="best")
        assert "data" in d
        d.clear()
        assert "data" not in d
        assert len(d) == 0
        d.new_key = 63
        assert "new_key" in d
        d.clear()
        assert len(d) == 0
        assert "new_key" not in d

    def test_dotdict_splats(self):
        d = DotDict(data=5)
        identity = lambda **kwargs: kwargs
        assert identity(**d) == {"data": 5}

    def test_dotdict_is_not_json_serializable_with_default_encoder(self):

        with pytest.raises(TypeError):
            json.dumps(DotDict(x=1))

    def test_dotdict_to_dict(self):
        d = DotDict(x=5, y=DotDict(z="zzz", qq=DotDict()))
        assert d.to_dict() == {"x": 5, "y": {"z": "zzz", "qq": {}}}

    def test_dotdict_to_dict_with_lists_of_dicts(self):
        d = DotDict(x=5, y=DotDict(z=[DotDict(abc=10, qq=DotDict())]))
        assert d.to_dict() == {"x": 5, "y": {"z": [{"abc": 10, "qq": {}}]}}


def test_as_nested_dict_defaults_dotdict():
    orig_d = dict(a=1, b=[2, dict(c=3)], d=dict(e=[dict(f=4)]))
    dotdict = as_nested_dict(orig_d)
    assert isinstance(dotdict, DotDict)
    assert dotdict.a == 1
    assert dotdict.b[1].c == 3
    assert dotdict.d.e[0].f == 4


def test_as_nested_dict_dct_class():
    orig_d = dict(a=1, b=[2, dict(c=3)], d=dict(e=[dict(f=4)]))
    dot_dict_d = as_nested_dict(orig_d, DotDict)
    dict_d = as_nested_dict(dot_dict_d, dict)
    assert type(dict_d) is dict
    assert type(dict_d["d"]["e"][0]) is dict


@pytest.mark.parametrize("dct_class", [dict, DotDict])
def test_merge_simple_dicts(dct_class):
    a = dct_class(x=1, y=2, z=3)
    b = dct_class(z=100, a=101)

    # merge b into a
    assert merge_dicts(a, b) == dct_class(x=1, y=2, z=100, a=101)

    # merge a into b
    assert merge_dicts(b, a) == dct_class(x=1, y=2, z=3, a=101)


@pytest.mark.parametrize("dct_class", [dict, DotDict])
def test_merge_nested_dicts_reverse_order(dct_class):
    a = dct_class(x=dct_class(one=1, two=2), y=dct_class(three=3, four=4), z=0)
    b = dct_class(x=dct_class(one=1, two=20), y=dct_class(four=40, five=5))
    # merge b into a
    assert merge_dicts(a, b) == dct_class(
        x=dct_class(one=1, two=20), y=dct_class(three=3, four=40, five=5), z=0
    )

    assert merge_dicts(b, a) == dct_class(
        x=dct_class(one=1, two=2), y=dct_class(three=3, four=4, five=5), z=0
    )


@pytest.mark.parametrize("dct_class", [dict, DotDict])
def test_merge_nested_dicts_with_empty_section(dct_class):
    a = dct_class(x=dct_class(one=1, two=2), y=dct_class(three=3, four=4))
    b = dct_class(x=dct_class(one=1, two=2), y=dct_class())
    # merge b into a
    assert merge_dicts(a, b) == a
    # merge a into b
    assert merge_dicts(b, a) == a


def test_as_nested_dict_works_when_critical_keys_shadowed():
    x = dict(update=1, items=2)
    y = as_nested_dict(x, DotDict)
    assert y.update == 1
    assert y.items == 2


def test_flatten_dict(nested_dict):
    flat = collections.dict_to_flatdict(nested_dict)
    assert flat == {
        collections.CompoundKey([1]): 2,
        collections.CompoundKey([2, 1]): 2,
        collections.CompoundKey([2, 3]): 4,
        collections.CompoundKey([3, 1]): 2,
        collections.CompoundKey([3, 3, 4]): 5,
        collections.CompoundKey([3, 3, 6, 7]): 8,
    }


def test_restore_flattened_dict(nested_dict):
    flat = collections.dict_to_flatdict(nested_dict)
    restored = collections.flatdict_to_dict(flat)
    assert restored == nested_dict


def test_call_flatdict_to_dict_on_normal_dict(nested_dict):
    restored = collections.flatdict_to_dict({"a": "b"})
    assert restored == {"a": "b"}


def test_restore_flattened_dict_with_dict_class():
    nested_dict = DotDict(a=DotDict(x=1), b=DotDict(y=2))
    flat = collections.dict_to_flatdict(nested_dict)
    restored = collections.flatdict_to_dict(flat)
    assert isinstance(restored, dict)

    restored_dotdict = collections.flatdict_to_dict(flat, dct_class=DotDict)
    assert isinstance(restored_dotdict, DotDict)
    assert isinstance(restored_dotdict.a, DotDict)
    assert restored_dotdict.a == nested_dict.a
