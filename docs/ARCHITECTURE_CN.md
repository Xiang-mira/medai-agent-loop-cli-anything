# 系统架构图

> 三张图描述系统的不同层面：整体组件关系、EM Loop 数据流、文件夹结构。

---

## 图 1：整体系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          medai-cli (CLI-Anything 风格)                  │
│                     统一入口，每个命令输出 JSON                          │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
┌────────────────┐   ┌─────────────────┐   ┌──────────────────────┐
│  AI 推理层     │   │  后处理层        │   │  Agent 控制层         │
│                │   │                 │   │                      │
│ TotalSegmentor │   │  ShapeKit       │   │  agent_controller    │
│ (104 类器官)   │──▶│  解剖约束修正   │──▶│  agent_state.json    │
│                │   │                 │   │  review_queue.jsonl  │
│ custom infer   │   │                 │   │                      │
└────────────────┘   └─────────────────┘   └──────────┬───────────┘
                                                       │
              ┌────────────────────────────────────────┤
              ▼                                        ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│  Label Verifier         │              │  RadThinking Trace       │
│                         │              │                          │
│  DSC 计算               │              │  4-step reasoning:       │
│  ├─ DSC ≥ 0.8 → accept  │              │  1. Observation          │
│  ├─ 0 < DSC < 0.8 → VLM │              │  2. Temporal Comparison  │
│  └─ empty→replace; disjoint→VLM │              │  3. Clinical Context     │
└────────────┬────────────┘              │  4. Conclusion           │
             │                           └─────────────────────────┘
             ▼
┌─────────────────────────┐
│  VLM Label Expert        │
│                          │
│  projection_builder      │
│  mask-centered 2D slice  │
│        ▼                 │
│  Ollama qwen2.5vl:7b     │
│  视觉模型看图判断         │
│  winner: A/B             │
│  confidence: 0.0–1.0     │
└────────────┬─────────────┘
             │
             ▼
┌─────────────────────────┐
│  AnnotationManager       │
│                          │
│  raw/          (原始)    │
│  predictions/  (预测)    │
│  updated/      (最优)    │
│  decisions.jsonl         │
└────────────┬─────────────┘
             │
             ▼
┌─────────────────────────┐
│  EM Loop                 │
│                          │
│  E-step: Label Verifier  │
│          + VLM           │
│  M-step: annotation      │
│          update (stub)   │
│  rounds_metrics.json     │
└─────────────────────────┘
```

---

## 图 2：ScaleMAI EM Loop 数据流

```
      CT 图像
         │
         ▼
 ┌───────────────┐   Round 0
 │ TotalSegmentor │──────────────────────────────────────────┐
 │   推理         │                                          │
 └───────────────┘                                          │
                                                            ▼
                                              ┌─────────────────────────┐
                                              │  predictions/round_000/  │
                                              │  pancreas.nii.gz         │
                                              │  liver.nii.gz  ...       │
                                              └──────────────┬──────────┘
                                                             │
 参考标注 (raw/)                                              │
 pancreas.nii.gz ──────────────────────────────────┐        │
                                                   ▼        ▼
                                          ┌─────────────────────────┐
                                          │      E-step              │
                                          │                          │
                                          │  Label Verifier          │
                                          │  DSC(ref, pred) = 0.71   │
                                          │  → send_to_vlm           │
                                          │          │               │
                                          │          ▼               │
                                          │  Projection Builder      │
                                          │  pancreas_axial.png      │
                                          │          │               │
                                          │          ▼               │
                                          │  qwen2.5vl:7b            │
                                          │  winner: A / B           │
                                          └──────────┬──────────────┘
                                                     │
                                          ┌──────────▼──────────────┐
                                          │  AnnotationManager       │
                                          │  apply_update(winner)    │
                                          │  updated/pancreas.nii.gz │
                                          │  decisions.jsonl ←─追加  │
                                          └──────────┬──────────────┘
                                                     │
                                          ┌──────────▼──────────────┐
                                          │      M-step              │
                                          │  (stub — 无 GPU)         │
                                          │  记录 would_retrain=True  │
                                          │  organs_updated: [panc.] │
                                          └──────────┬──────────────┘
                                                     │
                                              Round 1 (如有)
                                                     │
                                                     ▼
                                          ┌─────────────────────────┐
                                          │  rounds_metrics.json     │
                                          │  final_metrics:          │
                                          │  pancreas: {             │
                                          │    dice_final_vs_raw:    │
                                          │    final_annotation: ... │
                                          │  }                       │
                                          └─────────────────────────┘
```

---

## 图 3：文件夹 / 数据结构

```
medai_agent_loop_cli_anything_final/
│
├── agent-harness/                        ← Python 包 (pip install -e .)
│   └── cli_anything/medai/
│       ├── medai_cli.py                  ← 所有 CLI 命令入口
│       └── core/
│           ├── totalseg_runner.py        ← AI 推理封装
│           ├── shapekit_runner.py        ← ShapeKit 后处理
│           ├── label_verifier.py         ← DSC 路由
│           ├── projection_builder.py     ← mask-centered 2D slice overlay
│           ├── vlm_label_expert.py       ← Ollama VLM 调用
│           ├── annotation_manager.py     ← 版本化存储
│           ├── em_loop.py                ← mini EM loop
│           ├── agent_controller.py       ← 主 agent loop
│           ├── qc_checker.py             ← 质量检查
│           └── radthinking.py            ← reasoning trace
│
├── data/pants_real/                      ← 50 个真实 PanTS 病例
│   └── PanTS_00000023/                   ← 一个病例
│       ├── scans/PanTS_00000023/
│       │   ├── ct.nii.gz                 ← CT 图像
│       │   ├── report.txt                ← 临床报告
│       │   └── clinical.json             ← 临床变量
│       └── reference_labels/PanTS_00000023/segmentations/
│           ├── pancreas.nii.gz           ← 参考标注
│           ├── liver.nii.gz
│           └── ...
│
├── outputs/
│   ├── pants_batch_totalseg/             ← 50 case 批量推理输出
│   │   └── scan_outputs/PanTS_00000023/
│   │       └── raw_predictions/.../segmentations/
│   │           └── pancreas.nii.gz       ← TotalSegmentator 预测
│   │
│   └── em_loop_demo/                     ← EM loop 演示输出
│       ├── annotations/PanTS_00000023/
│       │   ├── raw/                      ← 原始参考标注 (只写一次)
│       │   ├── predictions/round_000/   ← 每轮预测
│       │   ├── updated/                  ← 当前最优标注
│       │   └── decisions.jsonl           ← 每次 VLM 决策日志
│       ├── vlm_outputs/round_000/
│       │   └── projections/
│       │       ├── pancreas_axial.png    ← 轴向对比图
│       │       └── pancreas_coronal.png  ← 冠状对比图
│       └── rounds_metrics.json           ← 完整 EM loop 日志
│
├── third_party/
│   ├── ShapeKit-main/                    ← 本地可选后处理工具
│   ├── PanTS-main/                       ← 本地可选数据集框架
│   └── CLI-Anything-reference/           ← CLI 封装参考
│
├── docs/
│   ├── MEETING_DEMO_REPORT_CN.md         ← 汇报文件（面向项目汇报）
│   ├── ARCHITECTURE_CN.md                ← 本文件
│   ├── PROJECT_THEORY_AND_REPORT_CN.md   ← 理论说明
│   └── COMMAND_CHEATSHEET.md             ← 命令速查
│
└── scripts/
    ├── batch_run_pants50.py              ← 50 case 批量脚本
    └── batch_eval_dice.py                ← Dice 批量评估
```
