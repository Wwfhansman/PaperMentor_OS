# PaperMentor OS 文档导航

## 1. 文档用途

本文件用于说明各类项目文档放在哪里，以及分别在什么场景下使用。

## 2. 核心文档

- [README.md](/Users/goucaicai/Desktop/PaperMentor_OS/README.md)
  用于查看项目总览、快速定位和仓库导航。

- [PRD.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/product/PRD.md)
  用于查看产品范围、用户问题、功能需求、评测维度和 MVP 边界。

- [ARCHITECTURE.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/architecture/ARCHITECTURE.md)
  用于查看稳定系统设计、agent 角色、编排逻辑和数据契约。

- [SKILL_REGISTRY.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/architecture/SKILL_REGISTRY.md)
  用于查看 skill 分类、metadata 规则、版本策略和评测要求。

- [DEVELOPMENT_GUIDE.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/engineering/DEVELOPMENT_GUIDE.md)
  用于查看逐步开发顺序、模块拆解、测试策略和实现约束。

- [DEVELOPMENT_PROGRESS.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/engineering/DEVELOPMENT_PROGRESS.md)
  用于查看当前真实开发进度、已完成模块、验证状态和下一步计划。

- [TECH_STACK.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/engineering/TECH_STACK.md)
  用于查看 Python 版本、框架选型、模型接入、BYOK 与成本策略。

- [ENV_SETUP.md](/Users/goucaicai/Desktop/PaperMentor_OS/docs/engineering/ENV_SETUP.md)
  用于查看 Mac 本地开发环境安装、Python 版本、虚拟环境和依赖初始化步骤。

- [references/README.md](/Users/goucaicai/Desktop/PaperMentor_OS/references/README.md)
  用于查看外部参考资料索引和架构灵感来源。

## 3. 推荐阅读顺序

新成员加入项目时，建议按以下顺序阅读：

1. `README.md`
2. `PRD.md`
3. `ARCHITECTURE.md`
4. `SKILL_REGISTRY.md`
5. `DEVELOPMENT_GUIDE.md`
6. `DEVELOPMENT_PROGRESS.md`
7. `TECH_STACK.md`
8. `ENV_SETUP.md`
9. `references/README.md`

## 4. 文档归属规则

- 产品层决策更新到 `PRD.md`
- 架构层决策更新到 `ARCHITECTURE.md`
- Skill 规则更新到 `SKILL_REGISTRY.md`
- 执行与实现细节更新到 `DEVELOPMENT_GUIDE.md`
- 实际开发进度更新到 `DEVELOPMENT_PROGRESS.md`
- 外部阅读笔记更新到 `references/` 下

## 5. 变更规则

如果一个新改动同时与 `PRD.md` 和 `ARCHITECTURE.md` 冲突，应将其视为重大项目决策，而不是日常微调。
