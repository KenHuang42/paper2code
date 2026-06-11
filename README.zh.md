# Paper2Code

将研究论文、技术文档或纯文字描述通过结构化、可验证的流水线转换为可运行的 PyTorch 或 TensorFlow 代码。

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 项目简介

Paper2Code 是一个多智能体流水线，能够将任何来源材料——PDF 论文、Markdown 技术文档、网页内容，甚至是一段粗略的想法——转化为完整、可运行的深度学习代码库。

该流水线围绕编译器风格的**中间表示（IR）**和**生成器与批评者之间的对抗性辩论循环**构建，确保架构准确性、张量形状一致性和执行正确性。

### 核心流水线

```
原始材料
      ↓
[阶段 1] 材料摄取 → source.md
      ↓
[阶段 2] 构建 IR → ir.json（结构化规格）
      ↓
[阶段 3] 模块规划 → plan.md（依赖关系图）
      ↓
[阶段 4] 生成与批评（辩论循环）
      │   生成器编写代码 → 批评者审查 → 迭代
      ↓
[阶段 5] AST 补丁修复 → patches.json（精准修复）
      ↓
[阶段 6] 执行与验证 → 沙箱环境冒烟测试
      ↓
可运行代码在 src/ 目录
```

---

## 主要特性

- **通用输入**：支持 PDF、Markdown、HTML、纯文本、网页链接，或聊天中的文字描述。
- **结构化 IR**：编译器风格的中间表示，将"理解"与"生成"解耦，有效减少幻觉。
- **对抗性辩论**：隔离的生成器和批评者子智能体在代码运行前审查其正确性。
- **AST 级补丁**：精准、最小化的代码修复，仅修改问题区域，保留已通过审查的代码。
- **沙箱执行**：自动检测依赖、创建临时虚拟环境、执行冒烟测试并输出结构化错误报告。
- **硬性限制**：辩论循环 ≤ 3 轮，执行重试 ≤ 2 次——防止无限循环，同时允许迭代优化。

---

## 项目结构

```
.
├── SKILL.md                     # Skill 定义与完整工作流规范
├── LICENSE                      # MIT 许可证
├── README.md                    # 英文文档
├── README.zh.md                 # 本文件
├── requirements.txt             # Python 依赖
├── references/
│   ├── ir-schema.md             # IR JSON 模式定义
│   ├── patch-schema.md          # AST 补丁 JSON 格式
│   └── code-patterns.md         # PyTorch 与 TensorFlow 代码模板
└── scripts/
    ├── extract_paper.py         # PDF 文本提取（PyMuPDF）
    ├── ast_patch.py             # 应用结构化 AST 级补丁
    └── run_code.py              # 沙箱执行，自动安装依赖
```

---

## 快速开始

### 安装

```bash
pip install PyMuPDF
```

或一次性安装所有依赖：

```bash
pip install -r requirements.txt
```

### 作为 AI Agent Skill 使用

将此仓库复制到智能体的 skills 目录（例如 `~/.agents/skills/paper2code/`）。智能体会自动加载 `SKILL.md` 中定义的工作流并执行结构化流水线。

触发词包括：
- "复现论文"
- "论文转代码"
- "把论文实现成代码"
- "帮我写这个模型的代码"
- "paper to code"
- "implement this paper"
- "build this model"

### 独立使用脚本

```bash
# 将 PDF 提取为结构化 Markdown
python scripts/extract_paper.py paper.pdf --output source.md

# 对生成的代码应用 AST 补丁
python scripts/ast_patch.py --code-dir ./src --patches patches.json

# 在沙箱环境中执行冒烟测试
python scripts/run_code.py --code-dir ./src --timeout 120
```

---

## 工作原理

### 阶段 1：摄取原始材料

任何输入——PDF、Markdown、粘贴的文本、网页链接或多个文件——都会被标准化为单个 `source.md`。

### 阶段 2：构建结构化 IR

从 `source.md` 中提取结构化的 JSON（`ir.json`），包含：
- 任务类型（分类、生成、检测等）
- 框架（PyTorch 或 TensorFlow）
- 模型架构（层、维度、连接关系）
- 数据流水线（数据集、预处理、增强）
- 训练配置（优化器、学习率、轮数）
- 评估指标
- 文件规划（模块到文件的映射）

如果原始材料信息不足，流水线会自动填充可推断的部分，并向用户询问缺失的关键字段（如输入维度、损失函数）。

### 阶段 3：规划代码模块

从 IR 的 `files` 字段构建依赖关系图。生成顺序遵循：

```
工具函数 → 模型 → 数据 → 训练 → 评估
```

### 阶段 4：生成与批评（辩论循环）

启动隔离的子智能体分别扮演生成器和批评者角色：

1. **生成器** 根据 IR 和规划将完整代码写入 `src/`。
2. **批评者** 对照 IR 规格审查代码，检查张量形状、导入、前向逻辑、损失函数、训练循环、设备处理和评估指标。
3. 如果批评者拒绝代码，问题会返回给生成器进行修正。

此循环最多运行 3 轮。上下文的分离确保了真正的对抗性审查。

### 阶段 5：应用 AST 补丁

批评者发现的问题被转换为结构化 JSON 补丁（`patches.json`），并通过 `scripts/ast_patch.py` 应用。支持的操作：

- `add_import` — 插入导入语句
- `insert_after` / `insert_before` — 行级插入
- `replace_line` — 单行替换
- `replace_function` — AST 级函数替换（不受行号漂移影响）
- `delete_lines` — 删除行范围

### 阶段 6：执行与验证

`scripts/run_code.py` 执行冒烟测试：
1. 扫描导入语句检测依赖
2. 创建临时虚拟环境
3. 自动安装所需包
4. 运行冒烟测试（1 个 batch 或 1 个 epoch）
5. 捕获 stdout、stderr 和 traceback
6. 输出结构化 JSON 结果

如果执行失败，流水线会反思错误、生成补丁并重试（最多 2 次）。

---

## 中间表示（IR）

IR 是整个流水线的核心产物。完整模式定义和示例（Transformer、ResNet）请参见 [`references/ir-schema.md`](references/ir-schema.md)。

关键字段：
- `components.model` — 架构、子模块、损失函数、输入/输出形状
- `components.data` — 数据集、预处理、数据加载器配置
- `components.training` — 优化器、学习率调度、轮数
- `components.evaluation` — 指标、测试循环
- `files` — 模块到文件的映射
- `dependencies` — 所需的 pip 包

---

## 代码模板

参见 [`references/code-patterns.md`](references/code-patterns.md) 了解生成过程中使用的地道 PyTorch 和 TensorFlow 模式，包括：

- 模型定义（nn.Module / keras.Model）
- 训练和评估循环
- 数据集与 DataLoader / tf.data
- 多头注意力与 Transformer 块
- 位置编码
- 学习率调度器
- 混合精度训练
- 设备处理

---

## 参与贡献

欢迎贡献！请随时提交 issue 或 pull request。

对于重大变更，请先提交 issue 讨论您希望修改的内容。

---

## 引用

如果您在研究或工作中使用了本项目，请考虑引用：

```bibtex
@software{paper2code,
  title = {Paper2Code: Convert Documents and Ideas to Runnable Deep Learning Code},
  year = {2026},
  url = {https://github.com/KenHuang42/paper2code},
  license = {MIT}
}
```

---

## 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。

---

## 致谢

- 设计灵感来源于编译器设计原理：结构化 IR、AST 变换和迭代优化。
- 为 OpenCode 智能体生态构建，但设计为通用 Skill，可被任何 AI 智能体或人类开发者使用。
