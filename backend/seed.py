#!/usr/bin/env python
"""
Seed — Personal AI OS Terminal.

就像 Claude Code 一样，一个命令进入你的智能空间。
  python seed.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text

GREEN = "#4ade80"
CYAN = "#22d3ee"
YELLOW = "#facc15"
GRAY = "#6b7280"
RED = "#ef4444"

BACKEND_DIR = Path(__file__).resolve().parent
SERVER_PROC = None
console = Console()


def start_server():
    global SERVER_PROC
    if SERVER_PROC:
        return True
    console.print("[dim]启动服务...[/dim]")
    SERVER_PROC = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=BACKEND_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    import httpx
    for _ in range(30):
        time.sleep(0.5)
        try:
            r = httpx.get("http://127.0.0.1:8000/", timeout=2)
            if r.status_code == 200:
                return r.json()
        except:
            pass
    return None


def stop_server():
    global SERVER_PROC
    if SERVER_PROC:
        SERVER_PROC.terminate()
        try: SERVER_PROC.wait(timeout=3)
        except: SERVER_PROC.kill()
        SERVER_PROC = None


def api_get(path):
    import httpx
    try:
        r = httpx.get(f"http://127.0.0.1:8000{path}", timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return {"error": "fail"}


def api_post(path, data=None):
    import httpx
    try:
        r = httpx.post(f"http://127.0.0.1:8000{path}", json=data or {}, timeout=120)
        r.raise_for_status()
        return r.json()
    except:
        return {"error": "fail"}


def show_welcome():
    day = (datetime.now() - datetime(2026, 7, 14)).days
    health = api_get("/")
    notes = health.get("vault_notes", 0) if health else 0

    console.clear()
    console.print()
    console.print(f"  [bold green]🌱 Seed[/bold green] [dim]— Personal AI OS[/dim]")
    console.print(f"  [dim]第 {day} 天 — 你与 Seed 共同成长的旅程[/dim]")
    console.print()

    t = Table.grid(padding=(0, 4))
    t.add_column()
    t.add_column()
    t.add_row(f"[{GREEN}]🧠[/] 记忆", f"[bold]{notes}[/]")

    graph = api_get("/graph")
    if isinstance(graph, dict) and "nodes" in graph:
        t.add_row(f"[{CYAN}]🔗[/] 知识", f"[bold]{graph['nodes']}[/] 节点 / [bold]{graph['edges']}[/] 边")

    world = api_get("/world")
    if isinstance(world, dict) and "world_model" in world:
        o = world["world_model"].get("owner", {})
        if o.get("career"):
            t.add_row(f"[{GREEN}]👤[/] 用户", o["career"])
        if o.get("current_goal"):
            t.add_row(f"[{YELLOW}]🎯[/] 目标", o["current_goal"][:40])

    console.print(t)
    console.print()
    console.print(f"  [{GREEN}]✓[/] [dim]Ready. 输入 /help 查看命令[/dim]")
    console.print()


def cmd_help():
    console.print()
    t = Table.grid(padding=(0, 2))
    t.add_column(style=f"bold {CYAN}")
    t.add_column(style="dim")
    for cmd, desc in [("/memory", "记忆花园"), ("/identity", "我是谁"),
                       ("/reflect", "每日反思"), ("/evolve", "进化循环"),
                       ("/stats", "系统状态"), ("/clear", "清屏"), ("/exit", "退出")]:
        t.add_row(cmd, desc)
    console.print(t)
    console.print()


def cmd_memory():
    console.print()
    console.print(f"[bold {GREEN}]🌱 记忆花园[/bold {GREEN}]")
    console.print()
    notes = api_get("/notes?limit=20")
    if not isinstance(notes, list):
        console.print("  [dim]记忆花园还在萌芽中...[/dim]\n")
        return
    prefs = [n for n in notes if "preference" in str(n.get("tags", [])).lower()]
    kbs = [n for n in notes if n not in prefs]
    if prefs:
        console.print(f"  [{GREEN}]🌱 嫩芽 — 偏好[/]")
        for n in prefs[:8]:
            console.print(f"    {n.get('name', '')}")
        console.print()
    if kbs:
        console.print(f"  [{CYAN}]🌿 生长 — 知识[/]")
        for n in kbs[:8]:
            console.print(f"    {n.get('name', '')}")
        console.print()
    if not prefs and not kbs:
        console.print("  [dim]记忆花园还在萌芽中...[/dim]\n")


def cmd_identity():
    console.print()
    console.print(f"[bold {GREEN}]🧬 我理解的你[/bold {GREEN}]")
    console.print()
    w = api_get("/world")
    if not isinstance(w, dict) or "world_model" not in w:
        console.print("  [dim]我还在了解你...[/dim]\n")
        return
    m = w["world_model"]
    o = m.get("owner", {})
    e = m.get("environment", {})
    t = Table.grid(padding=(0, 2))
    t.add_column(style="dim")
    t.add_column()
    if o.get("career"): t.add_row("职业", o["career"])
    if o.get("current_goal"): t.add_row("目标", o["current_goal"])
    if o.get("interests"): t.add_row("兴趣", ", ".join(o["interests"]))
    if e.get("main_lang"): t.add_row("语言", e["main_lang"])
    console.print(t)
    console.print()


def cmd_reflect():
    console.print(f"\n[{YELLOW}]🔍 反思中...[/]")
    d = api_post("/reflect", {})
    if isinstance(d, dict) and "error" not in d:
        console.print(f"\n[dim]{d.get('summary', '')}[/dim]\n")


def cmd_evolve():
    console.print(f"\n[{YELLOW}]🔄 进化中...[/]")
    d = api_post("/evolution", {})
    if isinstance(d, dict) and "error" not in d:
        console.print(f"  [{GRAY}]📊 {d.get('notes_reviewed', 0)} 条经验[/]")
        console.print(f"  [{GRAY}]🔗 衰减 {d.get('decayed_edges', 0)} 条边[/]")
        if d.get("reflection_summary"):
            console.print(f"  [dim]💭 {d['reflection_summary']}[/dim]")
        console.print()


def cmd_stats():
    h = api_get("/")
    g = api_get("/graph")
    w = api_get("/world")
    console.print()
    t = Table.grid(padding=(0, 2))
    t.add_column(style="dim")
    t.add_column(style="bold")
    if h: t.add_row("🧠 记忆", str(h.get("vault_notes", 0)))
    if isinstance(g, dict):
        t.add_row("🔗 节点", str(g.get("nodes", 0)))
        t.add_row("🔗 边", str(g.get("edges", 0)))
    if isinstance(w, dict) and "world_model" in w:
        o = w["world_model"].get("owner", {})
        if o.get("career"): t.add_row("👤 用户", o["career"])
    console.print(t)
    console.print()


def do_chat(text: str):
    import httpx
    with console.status(f"[{GREEN}]思考...[/]", spinner="dots"):
        try:
            r = httpx.post("http://127.0.0.1:8000/chat", json={"message": text}, timeout=120)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            console.print(f"\n  [{RED}]✗ 错误: {e}[/]\n")
            return

    console.print()
    reply = data.get("reply", "")
    console.print(Markdown(reply))
    console.print()

    bits = []
    if data.get("memory_saved"):
        bits.append(f"[{GREEN}]💾 已记忆 ({data.get('memory_category', '')})[/]")
    if data.get("experience_distilled"):
        bits.append(f"[{YELLOW}]📊 已蒸馏[/]")
    if data.get("context_notes", 0) > 0:
        bits.append(f"[{CYAN}]📚 检索 {data['context_notes']} 篇笔记[/]")
    if bits:
        console.print(f"[dim]{' | '.join(bits)}[/dim]")
        console.print()


def interactive():
    health = start_server()
    if not health:
        console.print(f"\n[{RED}]✗ 服务启动失败[/]\n")
        sys.exit(1)
    show_welcome()

    cmds = {
        "/help": cmd_help, "/memory": cmd_memory,
        "/identity": cmd_identity, "/reflect": cmd_reflect,
        "/evolve": cmd_evolve, "/stats": cmd_stats,
        "/clear": lambda: (console.clear(),
            console.print(f"\n[bold green]🌱 Seed[/bold green] — Personal AI OS[dim]\n[/dim]")),
    }

    while True:
        try:
            text = input(f"  [{GREEN}]>[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text in ("/exit", "exit"):
            break
        handler = cmds.get(text)
        if handler:
            handler()
        else:
            do_chat(text)

    console.print(f"\n[dim]🌱 再见。记住，我一直在成长。[/dim]\n")


if __name__ == "__main__":
    try:
        interactive()
    finally:
        stop_server()
