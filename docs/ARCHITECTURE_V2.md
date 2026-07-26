# Seed Architecture V2

## 系统架构（分层设计）

```
┌─────────────────────────────────────────────────────────┐
│                       你                                 │
│                   (User)                                 │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Interaction Layer                           │
│           FastAPI / CLI / Chat Interface                  │
│          (接收输入，返回响应，不包含任何智能)              │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Personality Layer        ←  NEW             │
│                                                          │
│  - 人格向量 (Personality Vector)                          │
│  - Communication Style (简洁/详细/正式/随意)              │
│  - Role Pattern (Researcher/Engineer/Investor/…)         │
│  - Work Rhythm (工作节奏识别)                             │
│  - 主动预测能力 ("你今晚要总结吗？")                      │
│                                                          │
│  功能：根据行为数据提炼人格特征，影响所有回答的风格        │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Behavior Layer           ←  NEW             │
│                                                          │
│  - Change Log (变化日志，非对话日志)                      │
│  - 行为观察器 (观察用户模式：何时编码/学习/总结)          │
│  - 变化检测器 (发现用户习惯/技能/偏好的转变)              │
│  - 节奏学习器 (学习用户的日常节奏)                        │
│                                                          │
│  功能：观察 → 提炼模式 → 更新 Personaity Vector          │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Memory Manager        ←  REFACTOR            │
│                                                          │
│  - 从"存对话"改为"存变化"                                  │
│  - 只保存值得记住的 Change                                 │
│  - 去重：相同信息不重复存储                                │
│  - 老化：旧知识自动降级                                    │
│                                                          │
│  四种学习：                                               │
│  ├─ Knowledge  → 存入 Obsidian/Knowledge/                 │
│  ├─ Experience → 存入 Obsidian/Experience/               │
│  ├─ Preference → 存入 Obsidian/Preferences/              │
│  └─ Behavior  → 更新 Personality Vector                  │
│                                                          │
│  每一条记录 = 一次 Change                                  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Knowledge Layer                              │
│                                                          │
│  Obsidian Vault (长期记忆/SSOT)                           │
│  ├─ Knowledge/    (结构化的知识笔记)                      │
│  ├─ Experience/   (经验教训)                              │
│  ├─ Preferences/  (用户偏好)                              │
│  └─ 自动积累，从空白开始                                  │
│                                                          │
│  索引：关键词 + 标签 + (未来) 向量嵌入                     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Retrieval Layer                              │
│                                                          │
│  4 层搜索管道：                                           │
│  1. Think — 分析问题类型                                  │
│  2. Obsidian — 搜索本地知识                              │
│  3. Skills — 检查匹配技能                                │
│  4. Web — 最后手段，结果写回                             │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Skills Layer                                 │
│                                                          │
│  按需加载的技能包：                                       │
│  ├─ python-coding/                                       │
│  ├─ writing/                                             │
│  └─ ...用户可自定义添加                                  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              LLM Layer                                    │
│                                                          │
│  当前：DeepSeek-v4-pro                                    │
│  可替换：Claude / GPT / 任何未来模型                      │
│  核心：推理引擎，不存储知识                               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Storage Layer                                │
│                                                          │
│  ├─ SQLite (结构化数据：Changes, Tasks, Goals)            │
│  ├─ Obsidian (长期知识：Markdown 文件)                    │
│  └─ (未来) 向量数据库 (语义搜索)                          │
└──────────────────────────────────────────────────────────┘
```

## 核心数据流

### 日常交互

```
用户输入
  ↓
1. Interaction Layer 接收
  ↓
2. Retrieval Layer 搜索 (Think → Obsidian → Skills → Web)
  ↓
3. LLM Layer 生成回答
  ↓
4. Memory Manager 分析变化
  ↓
5. Behavior Layer 更新模式
  ↓
6. Personality Layer 微调人格向量
  ↓
7. 返回 + 记录 Change
```

### Change 记录格式

```
Change #128
  type: behavior
  detected: 用户连续 5 天在 8:00-10:00 写代码
  pattern: morning-coding
  confidence: 0.85
  action: 更新 Personality.WorkRhythm
```

```
Change #129
  type: preference
  detected: 用户说"简洁一点"
  pattern: concise-style
  confidence: 0.9
  action: 更新 Personality.CommunicationStyle
```

## 从 V1 到 V2 的迁移路径

| 组件 | V1 状态 | V2 变化 |
|---|---|---|
| `memory/manager.py` | 存对话 + 分类 | 改存 Change，去重 |
| `memory/classifier.py` | 4 种分类 | +Behavior 分类 |
| `personality/` | 不存在 | **新建** |
| `behavior/` | 不存在 | **新建** |
| 现有 Obsidian 笔记 | 杂乱的测试数据 | 清理，从空白重新开始 |

## 不变的部分

- `core/` 层不变
- `domain/` 实体不变
- `infrastructure/database/` 不变
- `infrastructure/obsidian/vault.py` 不变
- `infrastructure/llm/deepseek_client.py` 不变
- `infrastructure/search/web_search.py` 不变
- `application/search/pipeline.py` 不变
- `application/skills/` 不变

## V2 新增文件

```
app/
├── personality/
│   ├── __init__.py
│   ├── vector.py          # 人格向量定义 + 更新
│   └── profile.md         # 人格档案（存 Obsidian）
├── behavior/
│   ├── __init__.py
│   ├── observer.py        # 行为观察器
│   ├── detector.py        # 变化检测器
│   └── rhythm.py          # 节奏学习器
└── memory/
    ├── (重构现有文件)
    └── change_log.py       # Change 日志
```

## 验证方式

1. 说"简洁一点" → Communication Style 更新
2. 连续 5 天早上写代码 → Work Rhythm 识别
3. 一段时间后 Agent 能主动预测："晚上需要帮你生成今天的总结吗？"
4. 查 Change Log 看到的是变化，不是聊天记录
