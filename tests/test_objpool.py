# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import objpool as mod  # noqa: E402
objpool = mod

from objpool.cli import run_ops  # noqa: E402


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_hex(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def test_acquire_release():
    p = objpool.ObjPool(4)
    o = objpool.acquire(p, "a")
    objpool.release(p, o)
    assert len(objpool.leaks(p)) == 0


def test_double_release_raises():
    p = objpool.ObjPool(2)
    o = objpool.acquire(p, "a")
    objpool.release(p, o)
    try:
        objpool.release(p, o)
    except ValueError:
        assert True
    else:
        assert False, "重复释放必须报错"
    assert p.double_release_errors == 1
    assert o.refs == 0, "重复释放不得把计数减成负数"


def test_recycle_on_zero_refs_resets_state():
    p = objpool.ObjPool(2)
    o = objpool.acquire(p, "a")
    o.dirty = True
    objpool.release(p, o)
    assert o.refs == 0
    assert o.tag == "" and o.dirty is False, "回收后状态必须重置干净"
    assert p.resets == 1
    assert len(objpool.leaks(p)) == 0


def test_reacquire_same_slot_clean():
    p = objpool.ObjPool(2)
    o1 = objpool.acquire(p, "x")
    o1.dirty = True
    slot = o1.slot
    objpool.release(p, o1)
    o2 = objpool.acquire(p, "y")
    assert o2.slot == slot, "连续申请应复用同一最小空闲槽"
    assert o2 is not o1, "复用槽位但不得返回已回收对象"
    assert o2.refs == 1 and o2.tag == "y" and o2.dirty is False
    objpool.release(p, o2)
    assert len(objpool.leaks(p)) == 0


def test_leaks_list_with_acquire_points():
    p = objpool.ObjPool(4)
    a = objpool.acquire(p, "a")
    b = objpool.acquire(p, "b")
    objpool.release(p, a)
    c = objpool.acquire(p, "c")
    lk = objpool.leaks(p)
    assert [e["tag"] for e in lk] == ["b", "c"]
    assert lk[0]["slot"] == b.slot and lk[0]["acquire_seq"] == 2
    assert lk[1]["slot"] == c.slot and lk[1]["acquire_seq"] == 3
    objpool.release(p, b)
    objpool.release(p, c)
    assert objpool.leaks(p) == []


def test_pool_exhausted():
    p = objpool.ObjPool(1)
    o = objpool.acquire(p, "only")
    try:
        objpool.acquire(p, "overflow")
    except objpool.PoolExhaustedError:
        assert True
    else:
        assert False, "容量耗尽必须报错"
    assert len(objpool.leaks(p)) == 1, "耗尽可能导致泄漏，但不得返回已回收对象"
    objpool.release(p, o)
    o2 = objpool.acquire(p, "again")
    assert o2.slot == o.slot
    objpool.release(p, o2)


def test_capacity_one_immediate_release():
    p = objpool.ObjPool(1)
    for i in range(3):
        o = objpool.acquire(p, "t%d" % i)
        assert o.slot == 0
        objpool.release(p, o)
    assert p.resets == 3
    assert p.peak == 1
    assert objpool.leaks(p) == []


def test_invalid_capacity():
    for bad in (0, -1):
        try:
            objpool.ObjPool(bad)
        except ValueError:
            assert True
        else:
            assert False, "非法容量必须报错"


def test_deterministic_report():
    ops = ["acquire:a", "acquire:b", "release:a", "release:b", "acquire:a"]
    r1 = run_ops(ops, 4)
    r2 = run_ops(ops, 4)
    assert r1 == r2, "同一操作序列两次结果必须一致"
    assert r1["peak"] == 2
    assert r1["leaks"] == 1
    assert r1["leak_list"] == [{"slot": 0, "tag": "a", "acquire_seq": 3}]
    assert r1["resets"] == 2
    assert r1["double_release_errors"] == 0


def test_report_counts_double_release():
    p = objpool.ObjPool(2)
    o = objpool.acquire(p, "a")
    objpool.release(p, o)
    for _ in range(3):
        try:
            objpool.release(p, o)
        except ValueError:
            pass
    assert p.double_release_errors == 3
