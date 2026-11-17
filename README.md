# 对象池引用计数

一个带引用计数、能检测泄漏并在回收后重置状态的对象池

## 保留签名

- `Obj`
- `ObjPool`
- `acquire(pool, tag)`
- `release(pool, obj)`
- `leaks(pool)`

## 自测

```
python -m pytest tests -q
python -m objpool.cli data/ops.json --out report.json
```
