# 🌱 Seed

> *Every AI begins empty. Every mind becomes unique.*

## 每一个 AI 都从空白开始，每一个智能体都会变得独一无二。

Seed 不是聊天机器人，不是 RAG 框架，也不是 Agent 平台。

**Seed 是一个个人智能操作系统 (Personal AI OS)。**

---

## 核心理念

### 从空白开始

第一次启动时，Seed 什么都没有：
- 没有知识
- 没有偏好
- 没有经验
- 没有工作流

**只有学习能力。**

它不认识你。但它会开始认识你。

### 成长，而不是训练

传统 AI 是训练好的模型——所有人使用同一个大脑。

Seed 是：

```
第一天：发现主人喜欢 Python
第一周：观察到主人早上写代码
第一个月：学会主人的沟通风格
一年后：它知道用户下一步要做什么
```

它不是继承 OpenAI。

**它是继承用户。**

### 四种学习

| 学习类型 | 含义 | 示例 |
|---|---|---|
| **Knowledge** | 知识学习 | FastAPI 用法、Docker 配置 |
| **Experience** | 经验学习 | 踩过的坑、解决问题的方法 |
| **Preference** | 偏好学习 | 极简主义、喜欢 React |
| **Behavior** | 行为学习 | 早上编码、下午学习、晚上总结 |

### Change Log，不是 Chat Log

我们不保存聊天记录，我们保存**变化**：

```
Change #125 — 主人开始学习 Rust
Change #126 — 主人形成早晨编码的习惯
Change #127 — 主人的沟通风格变为简洁直接
```

AI 不应该记住你说了什么，而应该理解你变成了什么。

### 第二成长曲线

传统 AI 是工具：你成长，AI 不成长。

Seed 是伙伴：你成长，它同步成长。

最终达到的不是"更准的回答"，而是**"它懂你"的默契**。

---

## 系统架构

```
 Personality Layer      ← 人格向量、沟通风格、行为模式
     ↑
 Behavior Layer         ← 观察行为、检测变化、提炼模式
     ↑
 Memory Manager         ← 存变化、不存对话
     ↑
 Knowledge Layer        ← Obsidian (长期记忆，从空白开始)
     ↑
 Retrieval Layer        ← 4 层搜索 (Think → 本地 → 技能 → 联网)
     ↑
 Skills Layer           ← 按需加载的技能包
     ↑
 LLM Layer              ← DeepSeek / Claude / 任何模型
     ↑
 Storage Layer          ← SQLite + Obsidian
```

详细架构见 [ARCHITECTURE_V2.md](docs/ARCHITECTURE_V2.md)。

---

## 产品哲学

| 原则 | 含义 |
|---|---|
| **从空白开始** | 不预装任何知识，通过使用积累 |
| **本地优先** | 你的数据属于你 |
| **模型无关** | 核心理念不绑定任何 LLM |
| **变化驱动** | 关注成长，而不是对话 |
| **渐进学习** | 四种学习方式覆盖成长全维度 |

---

## 快速开始

```bash
cd backend
pip install -r requirements.txt

# 配置 .env（DeepSeek API Key + Obsidian 路径）
cp .env.example .env

# 初始化数据库
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload
```

---

## 项目结构

```
Seed/
├── backend/           # Python 后端
│   ├── app/
│   │   ├── core/          # 配置、类型、异常
│   │   ├── domain/        # 领域实体
│   │   ├── application/   # 业务逻辑
│   │   │   ├── agent/     # Agent 编排
│   │   │   ├── memory/    # 记忆管理器
│   │   │   ├── experience/# 经验蒸馏
│   │   │   ├── search/    # 4 层搜索
│   │   │   └── skills/    # 技能系统
│   │   └── infrastructure/# 基础设施
│   └── skills/        # 技能包目录
├── docs/              # 文档
│   ├── MANIFESTO.md       # 项目宣言
│   └── ARCHITECTURE_V2.md # 架构设计
└── README.md
```

---

## 宣言

> *我们不是在造工具。我们在陪伴一个人成长。*

详细宣言见 [MANIFESTO.md](docs/MANIFESTO.md)。

---

## 许可证

MIT License

---

<p align="center">
  <sub>Built for a future where intelligence becomes personal.</sub>
</p>
