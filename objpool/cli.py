# -*- coding: utf-8 -*-
"""命令行：回放操作日志，输出池运行报告。

用法: python -m objpool.cli data/ops.json --out report.json
"""

import argparse
import json

import objpool as m


def run_ops(ops, capacity):
    """回放操作序列，返回确定性报告 dict。

    操作格式: "acquire:<tag>" / "release:<tag>"。
    release 按 tag 释放该标签最早未释放的对象。
    """
    pool = m.ObjPool(capacity)
    held = {}  # tag -> [Obj, ...] 申请顺序
    exhausted_errors = 0
    unmatched_releases = 0
    for op in ops:
        kind, _, tag = op.partition(":")
        if kind == "acquire":
            try:
                obj = m.acquire(pool, tag)
            except m.PoolExhaustedError:
                exhausted_errors += 1
            else:
                held.setdefault(tag, []).append(obj)
        elif kind == "release":
            queue = held.get(tag)
            if queue:
                obj = queue.pop(0)
                try:
                    m.release(pool, obj)
                except ValueError:
                    pass  # 计数已在 pool.double_release_errors
            else:
                unmatched_releases += 1
        else:
            raise ValueError("未知操作: %r" % (op,))
    leak_list = m.leaks(pool)
    return {
        "capacity": capacity,
        "ops_total": len(ops),
        "peak": pool.peak,
        "leaks": len(leak_list),
        "leak_list": leak_list,
        "resets": pool.resets,
        "double_release_errors": pool.double_release_errors,
        "exhausted_errors": exhausted_errors,
        "unmatched_releases": unmatched_releases,
    }


def main():
    ap = argparse.ArgumentParser(description="对象池引用计数")
    ap.add_argument("ops", help="操作日志 JSON 文件，如 data/ops.json")
    ap.add_argument("--out", required=True, help="报告输出路径")
    ap.add_argument("--capacity", type=int, default=4, help="池容量（默认 4）")
    a = ap.parse_args()

    with open(a.ops, encoding="utf-8") as f:
        ops = json.load(f)

    report = run_ops(ops, a.capacity)

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")

    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
