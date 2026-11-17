# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import objpool as mod  # noqa: E402

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
