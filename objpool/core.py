# -*- coding: utf-8 -*-
"""对象池引用计数"""

from dataclasses import dataclass, field


@dataclass
class Obj:
    """池中对象。"""
    slot: int
    refs: int = 1
    tag: str = ""
    dirty: bool = False


def acquire(pool, tag):
    """申请"""
    raise NotImplementedError("acquire 尚未实现")


def release(pool, obj):
    """释放"""
    raise NotImplementedError("release 尚未实现")


def leaks(pool):
    """列泄漏"""
    raise NotImplementedError("leaks 尚未实现")


class ObjPool:
    """class"""

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("ObjPool 尚未实现")

