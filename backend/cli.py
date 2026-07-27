#!/usr/bin/env python
"""
Seed CLI — 终端交互界面。

类似 Claude Code / Codex CLI 的对话式终端。
"""

import json
import os
import sys
from datetime import datetime

import httpx

BASE_URL = os.environ.get("SEED_URL", "http://localhost:8000")


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    clear()
    print("  ╔══════════════════════════════════════╗")
    print("  ║       🌱  Seed (Personal AI OS)      ║")
    print("  ╚══════════════════════════════════════╝")
    print()
    print(f"  连接: {BASE_URL}")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    print("  /help    查看命令")
    print("  /exit    退出")
    print()


def print_help():
    print()
    print("  ── 命令 ──")
    print("  /help      显示帮助")
    print("  /world     查看世界模型")
    print("  /graph     查看知识图谱")
    print("  /history   查看对话历史")
    print("  /reflect   运行每日反思")
    print("  /evolve    运行进化循环")
    print("  /notes     查看 Obsidian 笔记")
    print("  /clear     清屏")
    print("  /exit      退出")
    print()
    print("  直接输入文字即可对话")
    print()


def api_get(path: str) -> dict | None:
    try:
        resp = httpx.get(f"{BASE_URL}{path}", timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"\n  ❌ 请求失败: {e}")
        return None


def api_post(path: str, data: dict) -> dict | None:
    try:
        resp = httpx.post(
            f"{BASE_URL}{path}",
            json=data,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"\n  ❌ 请求失败: {e}")
        return None


def cmd_chat(message: str):
    result = api_post("/chat", {"message": message})

    if result is None:
        return

    print()
    print("  " + "─" * 50)

    reply = result.get("reply", "")
    print(f"  🌱 {reply}")

    print("  " + "─" * 50)

    # Show metadata
    meta = []
    if result.get("memory_saved"):
        meta.append(f"💾 已记忆({result.get('memory_category', '')})")
    if result.get("experience_distilled"):
        meta.append("📊 已蒸馏")
    if result.get("context_notes", 0) > 0:
        meta.append(f"📚 检索了 {result['context_notes']} 篇笔记")

    if meta:
        print(f"  {' | '.join(meta)}")

    print()


def cmd_world():
    print()
    data = api_get("/world")

    if data is None:
        return

    model = data.get("world_model", {})
    owner = model.get("owner", {})
    projects = model.get("projects", [])
    env = model.get("environment", {})

    print("  ── 世界模型 ──")
    print(f"  职业: {owner.get('career', '未知')}")
    print(f"  目标: {owner.get('current_goal', '未设定')}")
    print(f"  兴趣: {', '.join(owner.get('interests', [])) or '未知'}")
    print(f"  语言: {env.get('main_lang', '未知')}")
    print(f"  系统: {env.get('os', '未知')}")
    if projects:
        for p in projects:
            print(f"  项目: {p.get('name', '')} ({p.get('status', '')})")
    print()


def cmd_history():
    data = api_get("/history?limit=10")

    if data is None:
        return

    print()
    print("  ── 最近对话 ──")

    for item in data:
        action = item.get("action", "")[:80]
        outcome = item.get("outcome", "")
        time_str = ""
        if item.get("created_at"):
            time_str = item["created_at"][:10]
        print(f"  [{time_str}] [{outcome}] {action}")

    print()


def cmd_graph():
    data = api_get("/graph")

    if data is None:
        return

    print()
    print(f"  ── 知识图谱 ──")
    print(f"  节点: {data.get('nodes', 0)}")
    print(f"  边: {data.get('edges', 0)}")
    print()


def cmd_notes():
    data = api_get("/notes?limit=5")

    if data is None:
        return

    print()
    print("  ── Obsidian 笔记 ──")

    for note in data:
        name = note.get("name", "")
        tags = note.get("tags", [])
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        print(f"  📝 {name}{tag_str}")

    print()


def cmd_reflect():
    print()
    print("  🔄 运行每日反思...")

    data = api_post("/reflect", {})

    if data is None:
        return

    print(f"  📋 {data.get('summary', '')}")
    print()

    for key, label in [
        ("new_knowledge", "新知"),
        ("new_preferences", "新偏好"),
        ("new_skills", "新技能"),
        ("failure_patterns", "失败模式"),
        ("user_changes", "用户变化"),
    ]:
        items = data.get(key, [])
        if items:
            print(f"  [{label}]")
            for item in items:
                print(f"    - {item}")

    if data.get("actions_taken"):
        print(f"  [执行的动作]")
        for a in data["actions_taken"]:
            print(f"    - {a}")

    print()


def cmd_evolve():
    print()
    print("  🔄 运行进化循环...")

    data = api_post("/evolution", {})

    if data is None:
        return

    print(f"  回顾了 {data.get('notes_reviewed', 0)} 条经验")
    print(f"  衰减了 {data.get('decayed_edges', 0)} 条边")

    if data.get("reflection_summary"):
        print(f"  反思: {data['reflection_summary']}")

    print()


def main():
    print_header()

    # Check connection
    health = api_get("/")
    if health is None:
        print("  ❌ 无法连接到 Seed 服务")
        print(f"     请先启动: uvicorn app.main:app --reload")
        print()
        sys.exit(1)

    print(f"  ✅ 服务正常 | {health.get('vault_notes', 0)} 篇笔记")
    print()

    while True:
        try:
            text = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not text:
            continue

        if text == "/exit":
            print("\n  🌱 再见！\n")
            break
        elif text == "/help":
            print_help()
        elif text == "/world":
            cmd_world()
        elif text == "/history":
            cmd_history()
        elif text == "/graph":
            cmd_graph()
        elif text == "/notes":
            cmd_notes()
        elif text == "/reflect":
            cmd_reflect()
        elif text == "/evolve":
            cmd_evolve()
        elif text == "/clear":
            print_header()
        else:
            cmd_chat(text)


if __name__ == "__main__":
    main()
