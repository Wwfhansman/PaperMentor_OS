# PaperMentor OS

PaperMentor OS 是一个面向大学生的多智能体论文评审与指导系统。

它的目标不是替学生写论文，而是像导师初审一样，从多个维度诊断论文或研究草稿中的问题，并输出结构化指导意见，帮助学生加深自己的思考和修改过程。

## 项目价值

很多学生在论文写作中会反复遇到这几个问题：

- 不知道自己的研究问题是否足够清晰
- 不知道自己的论证链条是否完整
- 在论文早期拿不到足够及时的导师反馈

传统单模型 AI 工具往往更倾向于直接给答案或直接改写文本，这会削弱学生自己的思考深度。

PaperMentor OS 选择了另一条路径：

- 做多维度评审，而不是一次性回答
- 以指导为主，而不是代写
- 以证据支撑诊断，而不是泛泛点评
- 只在主观模块上引入选择性的多智能体协同

## 核心能力

- 评估选题价值与研究问题清晰度
- 评估论文章节结构与论证链路完整性
- 评估文献支撑与相关工作覆盖情况
- 评估创新性与研究深度
- 评估写作质量与格式规范
- 输出结构化的导师式评审报告与修改优先级建议

## 架构概览

PaperMentor OS 采用稳定的层级式架构：

- `ChiefReviewer` 负责总控编排与最终汇总
- 专项 worker agent 并行负责不同评审维度
- 主观模块在结论冲突时可以触发选择性辩论
- `Skill Registry` 管理 rubric、policy、schema 和领域规则
- `EvidenceLedger` 保证所有结论都能追溯到原文证据和评审标准

相比自由扩散式的 multi-agent swarm，这种结构更可控，也更容易长期维护。

## 比赛角度

- 痛点真实，而且高校场景普遍存在
- 教育价值明确，系统强调“指导”而不是“替代思考”
- 多智能体设计与论文评审场景天然匹配
- skill 机制让项目具备可维护性和扩展性
- 报告型输出适合比赛现场演示

## 仓库结构

```text
PaperMentor OS/
  README.md
  docs/
    architecture/
      ARCHITECTURE.md
      SKILL_REGISTRY.md
    product/
      PRD.md
    engineering/
      DEVELOPMENT_GUIDE.md
    roadmap/
      DOCUMENT_MAP.md
  references/
    README.md
    articles/
```

## 文档入口

- 产品需求文档：[PRD.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/product/PRD.md)
- 架构设计文档：[ARCHITECTURE.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/architecture/ARCHITECTURE.md)
- Skill 体系设计：[SKILL_REGISTRY.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/architecture/SKILL_REGISTRY.md)
- 开发文档：[DEVELOPMENT_GUIDE.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/engineering/DEVELOPMENT_GUIDE.md)
- 技术选型文档：[TECH_STACK.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/engineering/TECH_STACK.md)
- 环境搭建文档：[ENV_SETUP.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/engineering/ENV_SETUP.md)
- 文档导航：[DOCUMENT_MAP.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/roadmap/DOCUMENT_MAP.md)
- 参考资料索引：[references/README.md](/Users/goucaicai/Desktop/PaperMentor_OS/references/README.md)

## 建议的下一步

1. 先确认 PRD 边界，确保 V1 只聚焦“论文评审与指导”
2. 先实现报告 schema 和 evidence ledger 的核心契约
3. 先打通一条端到端流程，再扩展 agent 数量
4. 在大规模调 prompt 之前先建立离线评测样本

## V1 产品边界

PaperMentor OS V1 应该做到：

- 解析论文输入
- 执行多维度评审
- 识别关键问题
- 提供有优先级的修改指导

PaperMentor OS V1 不应该做到：

- 直接完整重写论文
- 一键生成最终论文
- 宣称对所有学科都具备专家级正确性判断能力

## 当前状态

当前仓库已经完成：

- 架构基线定义
- Skill Registry 基线定义
- 产品与开发文档整理
- 参考资料目录初始化
