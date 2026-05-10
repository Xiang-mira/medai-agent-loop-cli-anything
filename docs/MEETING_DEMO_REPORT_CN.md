# 汇报文件：医学 AI Agent Loop CLI 项目

> 本文件是面向项目汇报的项目说明与现场演示脚本。

---

## 一、项目定位

本项目不是从零训练一个大模型，而是：

**把多个医学 AI 工具封装成统一 CLI，再把这些 CLI 串成一个可自动运行的 agent loop。**

这正好对应项目参考资料的分工：

| 参考资料 | 在本项目中的角色 |
|----------|-----------------|
| **CLI-Anything** | 封装标准——每个工具统一输出 JSON，agent 才能读懂 |
| **ScaleMAI** | loop 的设计蓝图——Label Verifier → VLM → annotation update → retraining |
| **ShapeKit** | 后处理工具——修正 AI 分割的解剖结构错误 |
| **PanTS** | 数据集与评估标准——提供真实 CT、reference label、benchmark 格式 |
| **RadThinking** | 推理层——把单次分割升级为多时间点 longitudinal trace |

---

## 二、实现了什么（对应 ScaleMAI Figure 1）

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ScaleMAI Figure 1 流程                           │
│                                                                     │
│  CT 输入                                                            │
│    │                                                                │
│    ▼                                                                │
│  [AI 推理]  ←── TotalSegmentator (104 类器官分割)                   │
│    │              CLI: medai-cli infer                              │
│    │                                                                │
│    ▼                                                                │
│  [后处理]   ←── ShapeKit (解剖约束修正)                              │
│    │              CLI: medai-cli postprocess                        │
│    │                                                                │
│    ▼                                                                │
│  [Label Verifier] ←── DSC 计算，决定是否需要 VLM               ✅  │
│    │              CLI: medai-cli label-verify                       │
│    │                                                                │
│    ├─ DSC ≥ 0.8 → accept（无需 VLM）                               │
│    ├─ 0 < DSC < 0.8 → 发给 VLM Label Expert                        │
│    └─ annotation empty + prediction non-empty → auto_replace_candidate; both non-empty but DSC≈0 → VLM/review                             │
│                                                                     │
│    ▼                                                                │
│  [VLM Label Expert] ←── qwen2.5vl:7b 视觉模型，看 CT 对比图   ✅  │
│    │              CLI: medai-cli vlm-label-expert                   │
│    │              → 输出：winner A/B + confidence + reason          │
│    │                                                                │
│    ▼                                                                │
│  [Annotation Update] ←── AnnotationManager 版本化存储          ✅  │
│    │              raw/ predictions/round_NNN/ updated/              │
│    │                                                                │
│    ▼                                                                │
│  [EM Loop] ←── E-step + M-step stub                            ✅  │
│    │              CLI: medai-cli em-loop                            │
│    │              rounds_metrics.json                               │
│    │                                                                │
│    ▼                                                                │
│  [Human Review Queue] ←── uncertain → review_queue.jsonl       ✅  │
│    │                                                                │
│    ▼                                                                │
│  [RadThinking Trace] ←── 多时间点 longitudinal reasoning       ✅  │
│    │              CLI: medai-cli trace-build                        │
│    │                                                                │
│    ▼                                                                │
│  [Retraining/Continual Tuning] ←── stub（无 GPU，记录意图）    ⬜  │
└─────────────────────────────────────────────────────────────────────┘
```

**✅ = 已实现并可运行   ⬜ = stub（有日志，无 GPU 故不实际执行）**

---

## 三、核心模块一览

```
agent-harness/cli_anything/medai/core/
├── totalseg_runner.py      # AI 推理封装（TotalSegmentator / custom）
├── shapekit_runner.py      # ShapeKit 后处理封装
├── label_verifier.py       # DSC 计算 + 路由决策
├── projection_builder.py   # mask-centered 2D slice overlay（切片对比图）
├── vlm_label_expert.py     # Ollama VLM 调用 + 解析
├── annotation_manager.py   # 版本化 annotation 存储
├── em_loop.py              # mini EM loop
├── agent_controller.py     # 主 agent loop 控制器
├── qc_checker.py           # 分割质量检查
├── radthinking.py          # RadThinking trace 生成
└── human_review.py         # review queue 读写
```

**CLI 命令对应表：**

| 命令 | 功能 |
|------|------|
| `medai-cli doctor` | 环境检查 |
| `medai-cli infer` | AI 推理（TotalSegmentator/custom） |
| `medai-cli postprocess` | ShapeKit 后处理 |
| `medai-cli label-verify` | Label Verifier（DSC 路由） |
| `medai-cli vlm-label-expert` | VLM 视觉比较，选更好的 annotation |
| `medai-cli em-loop` | 完整 mini EM loop |
| `medai-cli agent-loop` | 多扫描 agent 控制器 |
| `medai-cli pants-eval-case` | Dice 评估 |
| `medai-cli trace-build` | RadThinking trace |

---

## 四、真实数据实验结果

- **数据集**：PanTS（胰腺 CT），50 个真实病例
- **模型**：TotalSegmentator（CPU 推理，无 GPU）
- **平均 Dice**：0.874（7 个器官，50 个 case）

| 器官 | 平均 Dice |
|------|-----------|
| aorta | ~0.97 |
| liver | ~0.96 |
| spleen | ~0.95 |
| kidney_left | ~0.94 |
| kidney_right | ~0.94 |
| pancreas | ~0.71 |
| stomach | ~0.68 |

胰腺和胃 Dice 偏低是正常的——这两个器官形状复杂、边界模糊，TotalSegmentator 本身在这两类器官上精度也更低。

---

## 五、VLM Label Expert 真实演示结果

案例：PanTS_00000023，胰腺

```
Label Verifier:
  DSC = 0.710（参考标注 109,842 voxel vs 预测 69,935 voxel）
  决策：DSC < 0.8 → 发给 VLM

VLM (qwen2.5vl:7b) 收到 CT 对比图后回答：
  winner: A
  confidence: 0.8
  reason: "Candidate A places the pancreas in a more anatomically
           plausible location, posterior to the stomach and anterior
           to the spine, as expected in the upper abdomen."

最终决策：keep_annotation_a（保留参考标注）
```

VLM 给出了有解剖学依据的判断，与 Dice 分析一致（参考标注更完整）。

---

## 六、现场演示步骤（约 5 分钟）

> 演示前提：已在 `agent-harness/` 目录，已激活 conda 环境，Ollama 已在后台运行。

### Step 1：环境确认（30 秒）

```powershell
python run_medai_cli.py --json doctor
```

输出：Python 版本、TotalSegmentator 是否可用、ShapeKit 路径。

---

### Step 2：Label Verifier——一次性 DSC 路由（30 秒）

```powershell
python run_medai_cli.py --json label-verify `
  --annotation-folder data\pants_real\PanTS_00000023\reference_labels\PanTS_00000023\segmentations `
  --prediction-folder outputs\pants_batch_totalseg\scan_outputs\PanTS_00000023\raw_predictions\PanTS_00000023_PanTS_00000023\segmentations `
  --organs pancreas,liver,spleen,kidney_left,kidney_right,aorta `
  --dsc-vlm-threshold 0.8
```

**讲解要点：** 看哪些器官 `decision: accept`（Dice 好），哪些 `send_to_vlm_label_expert`（Dice 不够好需要 VLM 判断）。

> **阈值说明：** 代码默认 `dsc_vlm_threshold=0.5`（对应 ScaleMAI 低 DSC 路由策略）。演示时使用 `--dsc-vlm-threshold 0.8` 是为了更严格地触发 VLM，方便可视化展示；两者均可，但要保持前后一致。

---

### Step 3：VLM Label Expert——让视觉模型看图判断（约 30 秒，结果已预先生成）

```powershell
python run_medai_cli.py --json vlm-label-expert `
  --ct-image data\pants_real\PanTS_00000023\scans\PanTS_00000023\ct.nii.gz `
  --annotation-a data\pants_real\PanTS_00000023\reference_labels\PanTS_00000023\segmentations\pancreas.nii.gz `
  --annotation-b outputs\pants_batch_totalseg\scan_outputs\PanTS_00000023\raw_predictions\PanTS_00000023_PanTS_00000023\segmentations\pancreas.nii.gz `
  --organ pancreas `
  --output-folder outputs\em_loop_demo\vlm_demo `
  --vlm-backend ollama `
  --vlm-model qwen2.5vl:7b `
  --dsc-vlm-threshold 0.8
```

**讲解要点：** 模型自动生成了左右对比图（`projections/pancreas_axial.png`），把图发给 qwen2.5vl，让它说哪边分割更合理。

---

### Step 4：EM Loop dry-run——展示完整流程结构（15 秒）

```powershell
python run_medai_cli.py --json em-loop `
  --case-id PanTS_00000023 `
  --ct-image data\pants_real\PanTS_00000023\scans\PanTS_00000023\ct.nii.gz `
  --annotation-folder data\pants_real\PanTS_00000023\reference_labels\PanTS_00000023\segmentations `
  --output-folder outputs\em_loop_demo `
  --organs pancreas,liver,spleen `
  --vlm-backend stub `
  --dry-run
```

**讲解要点：** 输出中 `rounds` 字段展示每轮的 inference → e_step → m_step 结构；`annotation_summary` 展示版本化存储；`m_step.note` 说明 GPU retraining 在真实 ScaleMAI 里的位置。

---

### Step 5：打开输出文件（1 分钟）

```
outputs/em_loop_demo/
├── annotations/PanTS_00000023/
│   ├── raw/              # 原始参考标注（只写一次）
│   ├── predictions/      # 每轮模型预测
│   ├── updated/          # 当前最优标注
│   └── decisions.jsonl   # 每次 VLM 决策日志
├── vlm_demo/projections/
│   ├── pancreas_axial.png    # 轴向对比图（左=参考，右=预测）
│   └── pancreas_coronal.png  # 冠状对比图
└── rounds_metrics.json       # 完整 EM loop 日志
```

---

## 七、诚实说明：没有实现的部分

| 未实现 | 原因 |
|--------|------|
| GPU retraining（M-step） | 无 GPU，有 stub 日志记录意图 |
| 完整 PanTS benchmark | TotalSegmentator 不是胰腺肿瘤专用模型 |
| LLM 自主决策 agent | 当前 loop 是确定性规则，非 LLM 规划 |
| 临床诊断推理 | 超出课程范围 |

---

## 八、一句话总结

> 本项目用 CLI-Anything 风格把 TotalSegmentator、ShapeKit、Label Verifier、VLM Label Expert 封装为统一 JSON CLI，再用 agent controller 把它们串成 Observe → Infer → QC → Label Verify → VLM → Annotation Update → EM Loop → Review Queue → RadThinking Trace 的可执行闭环，在 50 个真实 PanTS 病例上验证，平均 Dice 0.874。
