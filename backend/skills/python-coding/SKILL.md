---
name: python-coding
description: >
  Python 编码、脚本编写、调试方法和最佳实践。
  当用户要求编写、调试或优化 Python 代码时激活。
version: 1.0.0
keywords:
  - Python
  - 脚本
  - 代码
  - 函数
  - 类
  - 调试
  - pip
  - django
  - flask
  - fastapi
---

## Python 编码规范

- 遵循 PEP 8（使用 4 空格缩进，行宽 88 字符）
- 使用类型注解（`from __future__ import annotations`）
- 使用 `pathlib` 而非 `os.path`
- 异常处理使用具体异常类，而非裸 `except:`
- 使用 `logging` 而非 `print` 进行调试

## 项目结构

```
project/
├── src/
│   ├── __init__.py
│   └── main.py
├── tests/
│   └── test_main.py
├── pyproject.toml
└── README.md
```

## 常用模式

### 异步函数
```python
from __future__ import annotations
import asyncio

async def main():
    pass

asyncio.run(main())
```

### 数据类
```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
```

## 调试方法

1. 先确认错误信息和堆栈跟踪
2. 用 `logging` 输出关键变量值
3. 拆解问题：输入 → 处理 → 输出
4. 搜索类似问题前先理解根本原因
