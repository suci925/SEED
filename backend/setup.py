#!/usr/bin/env python
"""
Seed 快速启动脚本。

一键安装依赖、初始化数据库、启动服务。
"""

import subprocess
import sys
from pathlib import Path


def step(msg: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def run(cmd: list[str], cwd: Path | None = None) -> bool:
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode == 0


def main():
    root = Path(__file__).resolve().parent

    step("1/4  安装依赖")
    run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=root)

    step("2/4  检查 .env 配置")
    env_path = root / ".env"
    env_example = root / ".env.example"

    if not env_path.exists():
        print("  未找到 .env 文件，从 .env.example 复制...")
        env_example.write_text(
            env_example.read_text(),
            encoding="utf-8",
        )
        print("  请编辑 .env 填入你的 API Key 和 Obsidian 路径")
        return

    step("3/4  初始化数据库")
    if not run(["alembic", "upgrade", "head"], cwd=root):
        print("  ❌ 数据库迁移失败")
        return
    print("  ✅ 数据库迁移完成")

    step("4/4  启动服务")
    print()
    print("  运行以下命令启动：")
    print()
    print("  uvicorn app.main:app --reload")
    print()
    print("  或直接运行：")
    print()
    print(f"  {sys.executable} -m uvicorn app.main:app --reload")
    print()


if __name__ == "__main__":
    main()
