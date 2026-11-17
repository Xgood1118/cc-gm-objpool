# -*- coding: utf-8 -*-
"""对象池引用计数"""

import heapq
from dataclasses import dataclass


@dataclass
class Obj:
    """池中对象。"""
    slot: int
    refs: int = 1
    tag: str = ""
    dirty: bool = False


class PoolExhaustedError(RuntimeError):
    """池容量耗尽：所有槽位都在使用中。"""


def acquire(pool, tag):
    """申请

    从池中取一个空闲槽位，返回 refs=1 的新 Obj。
    池满时抛出 PoolExhaustedError，绝不返回已回收对象。
    """
    if not pool._free:
        raise PoolExhaustedError(
            "对象池已满（capacity=%d），无空闲槽位" % pool.capacity
        )
    slot = heapq.heappop(pool._free)
    pool._seq += 1
    obj = Obj(slot=slot, refs=1, tag=tag, dirty=False)
    pool._in_use[id(obj)] = (obj, pool._seq)
    if len(pool._in_use) > pool.peak:
        pool.peak = len(pool._in_use)
    return obj


def release(pool, obj):
    """释放

    引用计数减一；归零时回收槽位并重置对象状态。
    对未持有/已回收对象重复释放抛 ValueError。
    """
    entry = pool._in_use.get(id(obj))
    if entry is None or entry[0] is not obj:
        pool.double_release_errors += 1
        raise ValueError("重复释放或不属于本池的对象: %r" % (obj,))
    obj.refs -= 1
    if obj.refs > 0:
        return
    if obj.refs < 0:  # 防御：不应发生
        pool.double_release_errors += 1
        raise ValueError("引用计数已为负: %r" % (obj,))
    # 计数归零，回收：重置状态，槽位归还
    del pool._in_use[id(obj)]
    obj.tag = ""
    obj.dirty = False
    heapq.heappush(pool._free, obj.slot)
    pool.resets += 1


def leaks(pool):
    """列泄漏

    返回未回收对象清单（按申请顺序），每项含槽位、标签与申请序号。
    """
    return [
        {"slot": obj.slot, "tag": obj.tag, "acquire_seq": seq}
        for obj, seq in sorted(pool._in_use.values(), key=lambda e: e[1])
    ]


class ObjPool:
    """固定容量对象池，引用计数归零回收，回收即重置。"""

    def __init__(self, capacity):
        if not isinstance(capacity, int) or capacity < 1:
            raise ValueError("capacity 必须是 >= 1 的整数")
        self.capacity = capacity
        self._free = list(range(capacity))  # 最小堆：总是分配最小空闲槽
        self._in_use = {}  # id(obj) -> (obj, acquire_seq)
        self._seq = 0
        self.peak = 0  # 峰值占用
        self.resets = 0  # 回收并重置的次数
        self.double_release_errors = 0  # 重复释放报错次数
