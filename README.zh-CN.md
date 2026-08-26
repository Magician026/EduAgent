# EduAgent

[English](README.md) · [简体中文](README.zh-CN.md)

**把一份课程 PDF，变成一位知道你学会了什么、遗漏了什么，以及下一步该做什么的 AI 导师。**

大多数 PDF 问答工具在回答完一个问题后就结束了。EduAgent 更进一步：它基于你的课程讲义解释概念，展示答案对应的文件和页码，自动生成针对性练习，识别答案中的缺失要点和可能误解，并持续记录学习画像，让下一次学习真正比上一次更有针对性。

上传讲义，提出问题；选择一个概念进行练习；阅读形成性反馈；回到自己的薄弱点。EduAgent 希望让学习不再是反复翻找课件，而像是身边有一位耐心、会记住你学习状态的导师。

## EduAgent 解决什么问题？

```text
你的课程 PDF
      ↓
按页建立课程知识库
      ↓
带文件名和页码依据的课程解释
      ↓
围绕概念生成练习题
      ↓
反馈缺失要点和可能误解
      ↓
更新学习画像并决定下一步教学动作
```

核心体验可以概括为：

**理解 → 练习 → 获得反馈 → 调整下一步**

## 你可以用它做什么？

- **询问自己的课程内容**，得到贴合讲义上下文的回答。
- **查看答案依据**，通过文件名和页码回到原始课件复习。
- **按问题选择检索路径**：概览整份文档的问题会使用覆盖 PDF 各部分的结构化上下文；聚焦问题仍使用配置的 Top-K 检索。
- **切换讲解层级**，支持 Beginner、Standard 和 Advanced。
- **生成针对性练习**，支持选择题和简答题。
- **理解为什么需要改进**，查看遗漏的关键点和可能的概念误解。
- **追踪学习状态**，查看概念掌握度、薄弱概念、练习次数和得分。
- **获得透明的下一步建议**，在解释、举例、补强和提高题目难度之间进行教学调整。

## 当前状态：MVP 已完成，可以本地运行

EduAgent 的核心 MVP 已经实现并完成测试，覆盖从课程材料导入到学习进度查看的完整路径：

- 按页解析课程 PDF、分块和重复文件检测
- 基于课程内容的检索增强问答和页码引用
- 结构化模型输出
- 选择题与简答题生成
- 形成性答案评价
- 学习者画像、掌握度启发式和薄弱概念追踪
- 自适应教学策略
- Learn、Course Materials、Practice、Progress 和 About 页面
- 聊天模型与 Embedding 服务的独立配置

“MVP 已完成”表示软件闭环已经可以在本地使用，并不意味着它已经是面向所有用户的在线商业产品，也不代表已经通过教育实验科学证明学习增益。当前版本是单用户本地 MVP，暂不包含登录、多人隔离、扫描版 PDF OCR 和经过验证的知识追踪模型。

## 快速开始

### 1. 克隆并安装

```bash
git clone https://github.com/Magician026/EduAgent.git
cd EduAgent
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt
uv pip install -e .
```

支持 Python 3.11 及以上版本。如果不使用 `uv`，也可以使用普通虚拟环境安装相同的依赖文件。

### 2. 配置两类独立模型服务

EduAgent 使用一个服务生成讲解、题目和反馈，使用另一个服务生成 Embedding，用于课程 PDF 索引和问题检索。两者可以使用同一家服务，也可以分别使用不同服务。这意味着你可以用 DeepSeek 或 Kimi 负责教学对话，同时用独立的 Embedding 服务完成完整的 PDF 检索流程。

复制配置模板：

```bash
cp .env.example .env
```

推荐使用以下与供应商无关的配置：

```env
# 聊天 / 教学模型
EDUAGENT_LLM_API_KEY=你的聊天模型密钥
EDUAGENT_LLM_BASE_URL=https://你的聊天服务.example.com/v1
EDUAGENT_LLM_MODEL=你的聊天模型

# 用于 PDF 索引和问题检索的 Embedding 模型
EDUAGENT_EMBEDDING_API_KEY=你的Embedding服务密钥
EDUAGENT_EMBEDDING_BASE_URL=https://你的Embedding服务.example.com/v1
EDUAGENT_EMBEDDING_MODEL=你的Embedding模型
```

聊天服务需要提供 OpenAI-compatible Chat Completions 接口，Embedding 服务需要提供 OpenAI-compatible `/embeddings` 接口。

### Provider 配置示例

#### OpenAI 同时负责聊天和 Embedding

```env
EDUAGENT_LLM_API_KEY=sk-your-openai-key
EDUAGENT_LLM_BASE_URL=https://api.openai.com/v1
EDUAGENT_LLM_MODEL=gpt-4o-mini

EDUAGENT_EMBEDDING_API_KEY=sk-your-openai-key
EDUAGENT_EMBEDDING_BASE_URL=https://api.openai.com/v1
EDUAGENT_EMBEDDING_MODEL=text-embedding-3-small
```

#### DeepSeek 负责教学对话 + OpenAI 负责 Embedding

DeepSeek 提供 OpenAI-compatible Chat Completions 接口。当前官方示例使用 `https://api.deepseek.com`，模型示例包括 `deepseek-v4-flash` 和 `deepseek-v4-pro`。模型可用性请查看 [DeepSeek API 官方文档](https://api-docs.deepseek.com/)。

```env
EDUAGENT_LLM_API_KEY=你的DeepSeek API Key
EDUAGENT_LLM_BASE_URL=https://api.deepseek.com
EDUAGENT_LLM_MODEL=deepseek-v4-flash

EDUAGENT_EMBEDDING_API_KEY=sk-your-openai-key
EDUAGENT_EMBEDDING_BASE_URL=https://api.openai.com/v1
EDUAGENT_EMBEDDING_MODEL=text-embedding-3-small
```

#### Kimi / Moonshot 负责教学对话 + OpenAI 负责 Embedding

Kimi 提供 OpenAI-compatible Chat Completions 接口。国际服务地址为 `https://api.moonshot.ai/v1`；中国服务地址 `https://api.moonshot.cn/v1` 也由 Moonshot 官方文档提供。当前模型示例为 `kimi-k2.6`，可参考 [Kimi API 概览](https://platform.kimi.ai/docs/api/overview) 和 [模型列表](https://platform.kimi.ai/docs/models)。

```env
EDUAGENT_LLM_API_KEY=你的Moonshot API Key
EDUAGENT_LLM_BASE_URL=https://api.moonshot.ai/v1
EDUAGENT_LLM_MODEL=kimi-k2.6

EDUAGENT_EMBEDDING_API_KEY=sk-your-openai-key
EDUAGENT_EMBEDDING_BASE_URL=https://api.openai.com/v1
EDUAGENT_EMBEDDING_MODEL=text-embedding-3-small
```

#### 其他 OpenAI-compatible 服务

只要某个供应商或网关提供兼容的聊天和 Embedding 接口，就可以分别将聊天配置写入 `EDUAGENT_LLM_*`，将 Embedding 配置写入 `EDUAGENT_EMBEDDING_*`。

为了兼容旧版本，单一 Provider 配置仍支持 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL` 和 `OPENAI_EMBEDDING_MODEL`。

### 3. 启动应用

```bash
streamlit run app.py
```

打开 Streamlit 输出的本地地址，通常是 `http://localhost:8501`。

### 4. 第一次学习流程

1. 打开 **Course Materials**，上传课程讲义 PDF。
2. 点击 **Index selected PDFs**，等待索引完成。
3. 打开 **Learn**，针对讲义提出具体问题。
4. 展开来源卡片，检查回答对应的文件和页码。
5. 打开 **Practice**，选择概念并生成练习题。
6. 提交答案，阅读遗漏要点和误解反馈。
7. 打开 **Progress**，查看掌握度、薄弱概念和最近练习记录。

## 没有 API Key 时可以做什么？

应用仍然可以启动并显示配置提示和 About 页面。仓库还提供不调用模型服务的离线技术演示：

```bash
python examples/create_sample_pdf.py
PYTHONPATH=src python -m eduagent.evaluation.rag_evaluator \
  --dataset examples/evaluation_dataset.json
```

该演示用于检查文档解析、来源检索和延迟，不代表生产环境回答质量，也不代表已经证明学习效果。

## 下一步怎么推进？

### 先用一门真实课程试用

配置两类模型服务，上传一门课程，完整体验：**提问 → 引用 → 练习 → 反馈 → 进度**。重点观察引用是否准确、题目是否贴合课程，以及反馈是否真正改变了下一步学习内容。

### 从个人 MVP 变成稳定产品

- 增加多用户登录、数据隔离和可靠持久化
- 支持多课程、章节和概念关系管理
- 增加扫描课件 OCR
- 优化检索、题目质量、模型路由和调用成本
- 建立带隐私和数据留存策略的部署环境

### 验证真实学习效果

检索指标只能说明系统是否找到了相关内容，不能证明学习者是否学得更多。未来需要通过前测、后测和合适的对照条件，单独评估 EduAgent 对学习效果的影响。

## 技术概览

应用使用 Streamlit 构建界面，使用 PyMuPDF 进行按页 PDF 解析，使用 Chroma 保存本地向量，使用 SQLite 保存学习画像和学习记录，使用独立的 OpenAI-compatible 聊天适配器和 Embedding 适配器完成教学对话、题目生成、反馈和检索。下一步教学策略由透明、可解释的确定性策略控制，模型负责生成教学语言和结构化反馈。

运行数据保存在 `data/runtime/`，并被 Git 忽略。当前 MVP 面向本地单用户使用；在审查隐私、留存和访问要求前，不要上传敏感或受限制传播的课程材料。

## 项目文档

- [产品演示流程](docs/demo.md)
- [系统架构说明](docs/architecture.md)
- [技术评估和未来影响研究](docs/impact_study.md)

## 已知边界

- 当前是单用户本地 MVP，不提供登录和多人隔离。
- 本地 Chroma 和 SQLite 依赖运行环境，托管平台不保证本地磁盘永久保存。
- 暂不支持扫描版 PDF OCR。
- 自动评价用于形成性反馈，不应替代正式考试评分。
- 掌握度使用透明启发式方法，不是经过验证的知识追踪模型。
- 回答质量取决于课件文本质量、检索结果、Provider 兼容性和模型配置。
- 页码引用是可回查的证据；本 MVP 不能替代阅读原始材料或专家判断。

## License

本项目当前未单独声明开源许可证。公开分发或商用前，请补充许可证并审查第三方依赖条款。
