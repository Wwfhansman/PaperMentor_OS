# PaperMentor OS 参考资料说明

本目录用于存放与 PaperMentor OS 架构设计、产品思路和比赛答辩相关的外部参考资料。

## 目录规则

- `README.md` 用于维护资料索引和使用说明
- `articles/` 用于后续沉淀阅读笔记、摘要和整理后的资料内容

## 当前参考资料集合

### 1. Anthropic：How we built our multi-agent research system

链接：

- <https://www.anthropic.com/engineering/multi-agent-research-system>

参考价值：

- 适合作为 supervisor-worker 架构的参考
- 有助于说明为什么受控层级比自由 swarm 更适合严肃任务
- 与 `ChiefReviewer + specialized workers` 的设计高度相关

### 2. BettaFish GitHub 仓库

链接：

- <https://github.com/666ghj/BettaFish>

参考价值：

- 适合作为多角色协作与讨论式协调的参考
- 与项目里的选择性 debate 和竞争协同思路相关
- 有助于解释为什么“分歧处理”能改善主观评审质量

### 3. LangGraph Supervisor

链接：

- <https://changelog.langchain.com/announcements/langgraph-supervisor-a-library-for-hierarchical-multi-agent-systems>

参考价值：

- 适合作为层级化控制设计的参考
- 有助于支撑 manager-worker 分离的项目叙述
- 与稳定编排层设计直接相关

### 4. Google A2A：A new era of agent interoperability

链接：

- <https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/>

参考价值：

- 适合作为 capability discovery 与 metadata 路由的参考
- 与项目中的 skill registry 和未来 capability card 设计相关
- 有助于表达长期扩展性

## 如何使用本目录

建议用法：

- 在修改核心架构前先回看这些资料
- 学习机制，不要照搬术语
- 所有外部思路都必须回到真实产品需求上验证

建议后续补充的资料方向：

- debate-based review system 相关文章
- 教育 AI 安全与反代写边界相关资料
- rubric 驱动评测质量相关资料
