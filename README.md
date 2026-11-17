# 对象池引用计数

一个带引用计数、能检测泄漏并在回收后重置状态的对象池

## 保留签名

- `Obj`
- `ObjPool`
- `acquire(pool, tag)`
- `release(pool, obj)`
- `leaks(pool)`

## 行为约定

- **计数**：`acquire` 返回 `refs=1` 的新对象；`release` 将计数减一，归零才回收。
  回收时重置 `tag`/`dirty`，槽位归还空闲堆。重复 `release` 抛 `ValueError`，
  计数不会变负。
- **泄漏**：`leaks(pool)` 按申请顺序列出未回收对象的槽位、标签与申请序号。
- **容量耗尽**：抛 `PoolExhaustedError`（`RuntimeError` 子类），绝不返回已回收对象。
- **确定性**：槽位按最小空闲槽分配，同一操作序列两次运行报告完全一致。

## 自测

```
python -m pytest tests -q
python -m objpool.cli data/ops.json --out report.json
```

## 运行结果（data/ops.json，capacity=4）

| 指标 | 值 |
| --- | --- |
| 峰值占用 peak | 2 |
| 泄漏数 leaks | 1（slot 0, tag `a`, acquire_seq 3） |
| 重置次数 resets | 2 |
| 重复释放报错数 double_release_errors | 0 |
