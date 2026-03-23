# PaperMentor OS 环境搭建文档

## 1. 文档目的

本文件用于指导 PaperMentor OS 在本地 Mac 开发环境中的初始化配置。

目标是：

- 不使用系统自带 `Python 3.9`
- 统一项目运行时版本
- 为后续后端开发、模型接入和测试留出稳定环境

## 2. 推荐环境基线

建议开发基线如下：

- 操作系统：macOS
- Python：`3.11`
- 包管理：`pip`
- 虚拟环境：`venv`
- 代码编辑器：`VS Code` 或 `PyCharm`
- 版本管理：`git`

## 3. 为什么不要用系统自带 Python 3.9

原因：

- 系统 Python 不适合作为项目主运行时
- 当前主流 agent 框架普遍要求 `Python 3.10+`
- 直接依赖系统 Python 容易造成环境污染和依赖冲突

结论：

- 项目开发前应先安装独立的 `Python 3.11`

## 4. 安装 Python 3.11

推荐使用 Homebrew 安装。

### 4.1 检查是否已安装 Homebrew

在终端执行：

```bash
brew --version
```

如果终端返回版本号，说明已安装。

如果未安装，再去安装 Homebrew。

### 4.2 使用 Homebrew 安装 Python 3.11

```bash
brew install python@3.11
```

### 4.3 检查 Python 3.11 是否可用

```bash
python3.11 --version
```

如果输出类似 `Python 3.11.x`，说明安装成功。

## 5. 创建项目虚拟环境

进入项目目录：

```bash
cd ~/Desktop/PaperMentor_OS
```

创建虚拟环境：

```bash
python3.11 -m venv .venv
```

激活虚拟环境：

```bash
source .venv/bin/activate
```

激活成功后，终端前面通常会出现 `(.venv)`。

## 6. 升级基础工具

在虚拟环境中执行：

```bash
python -m pip install --upgrade pip setuptools wheel
```

## 7. 建议安装的第一批依赖

项目早期建议先安装这些基础依赖：

```bash
pip install fastapi uvicorn pydantic pyyaml python-dotenv
pip install openai langchain langgraph
```

如果后续需要测试：

```bash
pip install pytest
```

## 8. 环境变量建议

建议在项目根目录创建 `.env` 文件，用于存放：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `MODEL_NAME`

后续如果支持多供应商，也可以扩展更多配置项。

注意：

- `.env` 不应提交到公共仓库
- 如果要让 async run 在跨实例 `claim / resume` 后继续使用服务端托管凭证自动恢复，可额外配置：
  - `PAPERMENTOR_OS_SERVER_LLM_BASE_URL`
  - `PAPERMENTOR_OS_SERVER_LLM_API_KEY`
  - `PAPERMENTOR_OS_SERVER_LLM_MODEL_NAME`
  - `PAPERMENTOR_OS_SERVER_LLM_PROVIDER_ID`，默认 `openai_compatible`
  - `PAPERMENTOR_OS_SERVER_LLM_REVIEW_BACKEND`，默认 `model_with_fallback`
- 这组服务端变量只用于 failover / resume 恢复；请求体里的 request-scoped `llm.api_key` 仍不会持久化到 snapshot

## 9. 推荐的初始文件准备

开始编码前，建议项目具备：

- `.venv/`
- `.gitignore`
- `requirements.txt` 或 `pyproject.toml`
- `.env.example`

## 10. 推荐的 .gitignore 内容

至少应忽略：

```text
.venv/
__pycache__/
.DS_Store
.env
```

## 11. 验证环境是否准备完成

完成后，至少检查以下几项：

1. `python --version` 是否为 `3.11.x`
2. `which python` 是否指向 `.venv`
3. `pip list` 是否能看到已安装依赖
4. 能否正常导入 `fastapi`、`pydantic`、`langgraph`

例如：

```bash
python -c "import fastapi, pydantic, langgraph; print('ok')"
```

如果输出 `ok`，说明基础环境已可用。

## 12. 当前阶段的建议

你现在最适合先完成以下准备：

1. 安装 `Python 3.11`
2. 创建虚拟环境
3. 安装基础依赖
4. 生成 `.env.example`
5. 建立工程代码目录骨架

做完这些，才算真正进入开发状态。

补充说明：

- 当前 V1 输入优先支持 `docx`
- 后续再扩展 `pdf`
- 当前演示样例应围绕“计算机专业本科毕业论文草稿”准备
