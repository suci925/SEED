# 🌱 Seed

> **Seed is not another AI assistant.**
>
> **Seed starts with nothing, learns from experience, grows with its owner, and becomes a unique lifelong intelligence.**

**Seed 不是另一个 AI 助手。**

**它从空白开始，在陪伴中学习，在经验中成长，最终成为每个人独一无二的终身智能伙伴。**

---

## Seed Manifesto

### Every intelligence begins as a seed.

No one is born with memories. No one is born with experience. No one is born understanding another person. Neither should AI.

Seed does not pretend to know you. It grows with you. It learns from your decisions. It remembers your journey. It develops its own understanding of who you are.

Every Seed becomes different, because every life is different.

We are not building another chatbot. We are building a lifelong intelligence.

— 全文见 [MANIFESTO.md](docs/MANIFESTO.md)

---

## Seed 不是 AI 助手

它是一个 **Open Personal Intelligence Framework**。

- Claude 可以做推理引擎
- GPT 可以做推理引擎
- 本地模型也可以做推理引擎

而 Seed 始终是 Seed。

**模型会更新，但成长不会丢失。**

---

## 核心架构

```
                     Seed
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    Perception     Thinking        Action
        │              │              │
        ▼              ▼              ▼
  Context Layer  Decision Engine  Tool Router
        │              │              │
        └──────────────┼──────────────┘
                       ▼
              Learning Engine
             （整个系统的核心）
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    Memory        Experience     Personality
        │              │              │
        └──────────────┼──────────────┘
                       ▼
               Obsidian Vault
```

**Learning Engine 是核心，不是 LLM。**

LLM 只是推理引擎。真正让 Seed 成长的是学习引擎——它观察、提炼、反思、适应。

---

## 五项原则

| 原则 | 含义 |
|---|---|
| **用户拥有自己的智能** | 不是 OpenAI，不是我们，是用户 |
| **AI 应该学习，而不是假装** | 不知道就观察，不确定就成长 |
| **经验比聊天更重要** | 聊天可以删除，经验不能 |
| **成长比记忆更重要** | 记忆是过去，成长是未来 |
| **每一颗种子都会不同** | 因为每一个人生都不同 |

---

## 四种学习

| 类型 | 含义 | 示例 |
|---|---|---|
| **Knowledge** | 知识学习 | FastAPI 用法、Docker 配置 |
| **Experience** | 经验学习 | 踩过的坑、解决问题的方法 |
| **Preference** | 偏好学习 | 极简主义、喜欢 React |
| **Behavior** | 行为学习 | 早上编码、下午学习、晚上总结 |

---

## Identity（身份）

Seed 有自己的身份认知：

```yaml
Name: Seed
Owner: (用户)
Birthday: (首次启动日)
Mission: 帮助主人成长
Values: 诚实、好奇心、持续学习、尊重隐私
Relationship: 伙伴
```

## Reflection Engine（反思引擎）

不是总结聊天。而是总结成长。

每天反思：学到了什么？主人有什么变化？哪些回答可以更好？

真正成长的，不只是知识库，而是智能体本身。

---

## 开发原则

讨论任何功能时先问：

> **这个功能是在帮助 Seed 回答问题，还是在帮助 Seed 成长？**

---

## 快速开始

### 前置条件

- Python 3.12+
- [Obsidian](https://obsidian.md)（必需，Seed 用 Obsidian 作为长期记忆）
- 一个 LLM API Key（推荐 DeepSeek，国内可用，注册即送额度）

### 一键部署

```bash
# 1. 克隆
git clone https://github.com/suci925/SEED.git
cd SEED/backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
cp .env.example .env
# 编辑 .env，填入你的 API Key 和 Obsidian 仓库路径：
#   DEEPSEEK_API_KEY=sk-xxx
#   OBSIDIAN_VAULT_PATH=C:/path/to/your/vault

# 4. 初始化数据库
alembic upgrade head

# 5. 启动 🚀
python seed.py
```

### 也可以单独启动后端

```bash
cd backend
uvicorn app.main:app --reload
```

然后浏览器访问 `http://localhost:8000`，或：

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，我是小明"}'
```

---

<p align="center">
  <sub>We are not building a tool. We are growing alongside a person.</sub>
</p>
