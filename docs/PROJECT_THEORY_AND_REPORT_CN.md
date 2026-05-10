# 项目理论说明与汇报稿

## 项目真正要解决什么

项目参考资料不是让你从零训练一个大模型，而是让你理解：医学 AI 系统往往不是单模型推理，而是多个模型/工具组成的 workflow。为了让 agent 稳定调用这些工具，需要先把它们封装成统一 CLI。

## 资料关系

- CLI-Anything：学习怎么把不同工具包装成统一命令行接口。
- ScaleMAI：理解 medical AI loop。Figure 1 包含 model prediction、ShapeKit post-processing、VLM Label Expert、human review、ROC analysis、continual tuning。
- ShapeKit：ScaleMAI 里的 post-processing 工具，用来修正 AI segmentation 的解剖结构错误。
- PanTS：提供 CT segmentation 数据结构和 benchmark 背景。
- RadThinking：把任务从单次 detection/segmentation 升级为 longitudinal clinical reasoning trace。

## 1. ScaleMAI Figure 1 的流程是什么？

Prediction by public models / Label Verifier → ShapeKit post-processing → Label Expert/VLM 选择更好 annotation → human escalation → ROC analysis / continual tuning → 下一轮模型和数据共同改进。

## 2. 为什么这个 loop 可以被理解成 agent？

因为它不是单模型一次输出，而是：观察数据和预测结果，调用工具，检查质量，决定下一步，必要时升级到 VLM 或人工审核，再把结果反馈到下一轮。这个结构符合 Observe → Act → Check → Decide → Iterate。

## 3. ShapeKit 在这个流程中负责什么？

ShapeKit 不是 AI 模型本体，而是 post-processing/refinement tool。它接收 AI 模型输出的 organ masks，做 anatomy-aware correction，并输出 refined segmentation。

## 4. PanTS 数据集和 ShapeKit 有什么关系？

PanTS 提供医学 segmentation 任务背景和数据格式。ShapeKit 的输入正好是类似 PanTS 的 case folder：`case_id/segmentations/*.nii.gz`。

## 5. CLI-Anything 解决什么问题？

不同工具可能来自 Python、PyTorch、TensorFlow、脚本、API。agent 不能为每个工具写一套不同调用逻辑，所以要统一成 CLI：输入参数固定，输出 JSON，错误可检查，结果可复现。

## 本项目实现了什么

- 把 TotalSegmentator/custom infer 封装为 AI inference CLI。
- 把 ShapeKit 封装为 postprocess CLI。
- 把 PanTS-style `case_id/segmentations/*.nii.gz` 作为中间格式。
- 加入 RadThinking-style patient folder 和四步 trace。
- 加入 lightweight agent loop：Observe → Act → Check → Decide → Trace/Review → State logging。

## 没有夸大的地方

这不是完整 ScaleMAI。当前版本已经实现可执行 E-step，包括 Label Verifier、VLM Label Expert、AnnotationManager 和 annotation update；但还没有真实人工编辑 UI、GPU retraining、continual tuning checkpoint 和大规模专家验证。它是第一版可执行 agent-loop / mini EM annotation refinement infrastructure。

## 英文汇报

I implemented a CLI-Anything-style medical AI agent-loop prototype. I used TotalSegmentator or a custom command as the AI segmentation backend, ShapeKit as the post-processing tool, PanTS-style folders as the segmentation interface, and RadThinking-style patient folders as the longitudinal reasoning layer.

The agent controller observes each scan, calls the model and post-processing tool, checks output quality, decides whether to accept the trace or send it to a review queue, and saves an auditable agent_state.json. I would not claim this is the full ScaleMAI loop yet, because I have implemented an executable E-step with Label Verifier, VLM Label Expert, and annotation version updates, but I have not implemented a human editing UI, GPU retraining, continual tuning checkpoints, or large-scale expert validation. But it is the first executable CLI-based agent-loop infrastructure.
