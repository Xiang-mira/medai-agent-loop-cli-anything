# 资料学习总结

> 本文件总结项目参考的五份核心资料，说明每份资料的核心思想、关键设计，以及它在本项目中的具体落地方式。

---

## 资料一：CLI-Anything

### 核心思想

CLI-Anything 的核心主张是：**让 AI agent 能够稳定、可组合地调用任意命令行工具**。

传统 shell 工具的输出是给人看的文本——格式不固定、错误混在 stdout 里、无法被程序稳定解析。CLI-Anything 提出三条设计原则：

1. **统一 JSON 输出**：每个命令都通过 `--json` flag 输出结构化 JSON，agent 可以直接 `json.loads()` 解析。
2. **SKILL.md 自描述**：每个工具附带一份 `SKILL.md`，告诉 agent 这个工具能做什么、命令签名是什么、输出字段有哪些。Agent 无需硬编码调用方式。
3. **可组合性**：工具之间通过 JSON 传递上下文，而不是通过管道传递文本。一个工具的 `output_folder` 字段直接成为下一个工具的 `--input-folder` 参数。

### 关键设计

- `--json` flag：所有命令加上这个 flag 后切换为 JSON 输出模式
- `doctor` 命令：自检环境，输出工具链是否就绪
- `SKILL.md`：机器可读的工具能力说明书

### 在本项目中的落地

```
medai-cli --json doctor          → 输出 JSON 格式的环境检查
medai-cli --json agent-loop ...  → 输出 JSON 格式的完整 agent 状态
medai-cli --json vlm-label-expert ... → 输出 JSON 格式的 VLM 决策
```

本项目的 `medai-cli` 完全遵循 CLI-Anything 风格：
- 所有主要命令都支持 `--json` 输出
- `agent-harness/cli_anything/medai/skills/SKILL.md` 是工具的自描述文件
- 输出 JSON 包含 `status`、`stage`、`implemented_steps` 等固定字段，agent 可稳定解析

---

## 资料二：ScaleMAI

### 核心思想

ScaleMAI 解决的是：**如何用 AI + 人工协作，批量生产高质量医学分割标注**。

核心发现：纯人工标注慢且贵，纯模型标注精度不够，两者结合——用模型给出初始分割，再用一套**质量控制 + 专家审核 + 模型微调**的闭环不断提升——才能规模化。

Figure 1 描述的 pipeline：

```
CT → AI 推理 → Label Verifier（DSC 路由）
               ├─ DSC ≥ 高阈值  → accept（不需要人工）
               ├─ 中等 DSC / DSC=0 且两者均非空 → VLM Label Expert（视觉模型看图判断）
               └─ DSC=0 且 annotation 为空、prediction 非空 → auto_replace candidate；两者均非空但 DSC=0 → VLM/review
                         ↓
               AnnotationManager（版本化存储）
                         ↓
               EM Loop: E-step（标注质量评估）+ M-step（模型微调）
                         ↓
               Human Review Queue（置信度低的案例人工审核）
```

### 关键设计

- **Label Verifier**：用 Dice Similarity Coefficient (DSC) 量化两个分割的差异，然后基于阈值路由
- **VLM Label Expert**：当 DSC 处于中间区域时，不依赖人工，而是让视觉语言模型看 CT 切片对比图来判断哪个分割更合理
- **AnnotationManager**：维护 `raw/`（原始）、`predictions/round_NNN/`（每轮模型预测）、`updated/`（当前最优）三级存储
- **EM Loop**：E-step 更新标注（哪个更好），M-step 用更新后的标注微调模型（本项目中是 stub，无 GPU）

### 在本项目中的落地

| ScaleMAI 概念 | 本项目实现 |
|---------------|-----------|
| Label Verifier | `label_verifier.py` + `medai-cli label-verify` |
| VLM Label Expert | `vlm_label_expert.py` + `medai-cli vlm-label-expert`（Ollama qwen2.5vl:7b） |
| AnnotationManager | `annotation_manager.py`，三级存储 + `decisions.jsonl` |
| EM Loop | `em_loop.py` + `medai-cli em-loop` |
| Human Review Queue | `human_review.py` + `review_queue.jsonl` |
| M-step retraining | stub（无 GPU），记录 `would_retrain=True` |

真实 VLM 演示结果（PanTS_00000023，胰腺，DSC=0.710）：
```
winner: A, confidence: 0.8
reason: "Candidate A places the pancreas in a more anatomically plausible
         location, posterior to the stomach and anterior to the spine."
```

---

## 资料三：RadThinking

### 核心思想

RadThinking 解决的是：**如何把单次静态分割升级为多时间点、有推理链路的纵向诊断辅助**。

核心洞察：放射科医生看 CT 不是只看一张图，而是：
1. **观察**（Observation）：这次扫描里，目标器官/病变在哪里、多大、HU 值多少？
2. **对比**（Temporal Comparison）：和上次相比，是变大了（GROWING）、稳定（STABLE）、还是消失了（RESOLVED）？
3. **结合临床**（Clinical Context）：报告里有没有可疑词汇？临床变量（CA19-9 等）是否异常？
4. **结论**（Diagnostic Conclusion）：综合以上，复杂程度是 PERCEPTUAL / TEMPORAL / INTEGRATIVE / AMBIGUOUS？

这四步构成 RadThinking 的 reasoning trace。

### 关键设计

- **Longitudinal structure**：患者数据按时间排列，多次扫描组成时间序列
- **Negation-aware report parsing**：报告中 "no suspicious lesion" 不应被当作"有可疑病变"。需要识别否定词
- **Complexity labeling**：根据时态变化 + 报告内容，自动给 trace 打上复杂度标签

### 在本项目中的落地

- `radthinking.py`：实现了完整的四步 reasoning trace
- 否定感知：`_NEGATION_RE` 正则，检查词前 60 字符是否有 "no/not/without/negative for/absence of/excluded/ruled out"
- `build_reasoning_trace()` 输出的 `radthinking_trace` 字段包含四步结构
- `agent-loop` 最终 JSON 中有 `radthinking_style_reasoning` 字段，摘要显示每次扫描的时态标签和可疑词
- `medai-cli trace-build`：单独构建一次 trace
- `medai-cli radthinking-check`：检查患者文件夹是否满足纵向结构

---

## 资料四：PanTS

### 核心思想

PanTS（Pancreatic Tumor Segmentation）是专注于**胰腺肿瘤 CT 分割**的数据集和评估框架。

核心贡献：
- 提供标准化的患者文件夹格式（`case_id/scans/case_id/ct.nii.gz` + `case_id/reference_labels/case_id/segmentations/*.nii.gz`）
- 提供基准 Dice 评分和评估脚本
- 包含 50 个真实患者 CT 和手动标注

### 关键设计

- **文件夹格式**：扫描图像和参考标注分离存放，方便独立替换
- **评估脚本**：`batch_eval_dice.py` 计算每个器官的 DSC，并汇总跨 case 均值
- **多器官**：除胰腺外还包含 liver、spleen、kidney_left、kidney_right、aorta、postcava 等参考标注

### 在本项目中的落地

- 50 个真实 PanTS 病例已导入 `data/pants_real/`
- `pants_utils.py`：PanTS 文件格式解析
- `medai-cli pants-import-case`：单病例导入
- `medai-cli pants-eval-case`：单病例 Dice 评分
- `scripts/batch_run_pants50.py`：50 case 批量推理
- `scripts/batch_eval_dice.py`：批量 Dice 评估

实验结果（TotalSegmentator CPU，50 case）：

| 器官 | 平均 Dice |
|------|-----------|
| aorta | ~0.97 |
| liver | ~0.96 |
| spleen | ~0.95 |
| kidney_left | ~0.94 |
| kidney_right | ~0.94 |
| pancreas | ~0.71 |
| stomach | ~0.68 |
| **7 器官均值** | **~0.874** |

胰腺和胃 Dice 偏低是预期内的——这两个器官形状复杂、边界模糊。

---

## 资料五：ShapeKit

### 核心思想

ShapeKit 解决的是：**AI 分割结果的解剖合理性后处理**。

纯 AI 模型输出的分割可能出现：左右肾标反了、胰腺飞到了胸腔、两个独立的 mask 合并成了一个——这些错误在 DSC 上可能还可以，但在临床上是不可接受的。ShapeKit 引入**解剖约束**（anatomical constraints）来修正这类错误。

### 关键设计

- **Anatomy-aware post-processing**：用解剖学先验知识（器官的正常位置范围、大小范围、左右关系）约束模型输出
- **可配置的约束规则**：通过配置文件指定哪些器官需要哪些约束
- **与推理后端解耦**：ShapeKit 是独立工具，接受任意分割结果作为输入

### 在本项目中的落地

- `shapekit_runner.py`：ShapeKit 调用封装
- `medai-cli postprocess`：单次后处理命令
- `agent-loop` 中 `--postprocess shapekit` 参数触发 ShapeKit 后处理
- `batch_run_pants50.py` 中 `--shapekit` flag 对全部 50 case 开启后处理
- ShapeKit 位于 `third_party/ShapeKit-main/`

---

## 五份资料的协同关系

```
PanTS           → 提供真实 CT 数据和评估标准
TotalSegmentator ← 在 PanTS CT 上做初始分割
         ↓
ShapeKit         ← 解剖约束后处理（CLI-Anything 风格调用）
         ↓
Label Verifier   ← ScaleMAI 核心：DSC 路由
         ↓
VLM Label Expert ← ScaleMAI 核心：视觉模型判断
         ↓
AnnotationManager ← ScaleMAI 核心：版本化存储
         ↓
EM Loop          ← ScaleMAI 核心：E-step + M-step 闭环
         ↓
RadThinking Trace ← 四步推理链路，纵向比较
         ↓
Human Review Queue ← 低置信度案例人工审核
         ↓
medai-cli        ← CLI-Anything 风格统一 JSON 接口
```

每份资料不是孤立使用的，而是像积木一样拼接：PanTS 提供数据 → ShapeKit 提供后处理 → ScaleMAI 提供 pipeline 逻辑 → RadThinking 提供推理层 → CLI-Anything 提供统一接口。

---

## 本项目与原始资料的差距（诚实说明）

| 原始资料能力 | 本项目实现状态 |
|-------------|--------------|
| ScaleMAI GPU retraining | stub（无 GPU） |
| 完整 PanTS benchmark（tumor 分割） | TotalSegmentator 非肿瘤专用模型，Dice 偏低符合预期 |
| LLM 自主规划 agent | 确定性规则 loop，非 LLM 规划 |
| RadThinking LLM 报告提取 | 规则 regex，非 LLM |
| 临床诊断推理 | 不做诊断 |

这些差距有的是硬件限制（无 GPU），有的是课程范围限制（不做临床诊断），都在 `MEETING_DEMO_REPORT_CN.md` 中如实说明。
