# 模型与数据选择说明

## 1. 为什么第一版用了 TotalSegmentator？

TotalSegmentator 是免费、开源、可直接命令行调用的 CT 解剖结构分割模型/工具。它适合作为第一版 `infer` backend，因为当前任务首先是“把一个 AI 模型/工具封装成 CLI”，而 TotalSegmentator 可以稳定测试：

- CLI 是否能调用外部模型；
- 模型输出是否能转换成 `case_id/segmentations/*.nii.gz`；
- ShapeKit 是否能接收这些 masks 做后处理；
- agent controller 是否能读取 JSON、做 QC、进入 review queue。

但它不是 pancreatic tumor-specific model。它更适合做工程可运行原型，不适合作为最终 PanTS tumor benchmark 的科学模型。

## 2. 什么模型更匹配 PanTS？

更匹配的是 pancreatic lesion / PanTS-specific segmentation model，例如 PanTS benchmark 中的 nnU-Net、MedFormer、R-Super 等。当前 CLI 已通过 `--backend custom --model-command "..."` 支持替换任意模型。也就是说：外层 agent loop 不需要改，只需要把模型命令换成目标模型或公开 checkpoint 的推理脚本。

## 3. 本地可选 PanTS zip 为什么不能直接跑真实数据？

`PanTS-main.zip` / PanTS repository 是 GitHub 仓库，包含 README、数据结构说明和下载脚本；它不是完整 CT 数据本体。真实 PanTS/PanTSMini 数据需要另外下载，官方说明需要约 300GB 存储。

可先运行：

```powershell
python run_medai_cli.py --json pants-info
python run_medai_cli.py --json pants-check --pants-root third_party\PanTS-main
```

如果 `pants-check` 显示没有 ImageTr/ImageTe cases，说明还没有下载真实 CT。

## 4. RadThinking PDF 能不能直接提取出真实 20,362 个 CT？

不能。PDF 只是论文说明，不包含实际 CT、报告、临床变量或 pathology JSON 文件。它告诉我们应该实现什么数据结构：patient-level longitudinal scans + report + clinical variables + pathology + four-step reasoning trace。当前代码已经按这个结构实现了 `radthinking-check`、`trace-build` 和 `agent-loop`。

## 5. 当前 synthetic demo 的意义是什么？

它是 smoke test，不是医学实验。作用是先证明 CLI、ShapeKit、QC、decision、trace、review queue 全链路能跑通。等真实 PanTS/RadThinking 数据下载或获得真实数据后，替换 `--patient-folder` 即可。

## 6. 方案 A：PanTS-small-demo，不下载全量 300GB

这次采用的正式策略是：**不更换项目指定的数据集主线，仍然以 PanTS 为目标数据集，但先只导入少量真实 PanTS 病例**。

原因：PanTS 官方脚本按大块 tar 包下载，其中 ImageTr 被分成 9 个每块约 1000 个病例的 tar.gz，Label 则是整体 label 压缩包。因此官方脚本不等价于“直接下载 1 个病例”。本项目不假设你已经拥有 300GB 存储，而是提供两个导入命令：

```powershell
python run_medai_cli.py --json pants-import-case `
  --pants-root third_party\PanTS-main `
  --case-id PanTS_00000001 `
  --output-root data\pants_small
```

这个命令适合你已经下载/解压了某个 PanTS case 的情况。

如果本地环境或公开数据源提供了一个 `ct.nii.gz` 和一个 `segmentations` 文件夹，可以用：

```powershell
python run_medai_cli.py --json pants-import-files `
  --ct D:\path\to\ct.nii.gz `
  --label-folder D:\path\to\segmentations `
  --output-root data\pants_small `
  --patient-id PanTS_00000001
```

导入后会生成：

```text
data/pants_small/PanTS_00000001/
├── metadata.json
├── pathology.json
├── scans/PanTS_00000001/
│   ├── ct.nii.gz
│   ├── report.txt
│   └── clinical.json
└── reference_labels/PanTS_00000001/segmentations/*.nii.gz
```

这样它就变成了当前 CLI 能处理的 RadThinking-style patient folder，同时保留 PanTS reference masks，用于后续简单 Dice sanity check。

## 7. 为什么 RadThinking PDF 不能“提取出真实数据”？

论文 PDF 里写了数据规模、字段设计、构建流程和四步 reasoning trace，但它不是数据仓库，也不包含 20,362 个 CT 文件、9,131 个病人文件夹、report 文本、clinical JSON 或 pathology JSON。论文里的数字和图表不能还原成原始医学图像，因为 CT NIfTI 是大体积二进制医学影像文件，报告和临床变量也需要单独的数据发布包。

所以正确做法是：

- 用 RadThinking PDF 学习数据结构和 reasoning trace 设计；
- 在代码中实现 `observation / temporal / context / conclusion` 四步接口；
- 等真实 RadThinking 风格数据或公开数据下载入口可用后，再把真实 patient folder 接进来。

这和 PanTS 的处理方式不同：PanTS 已经有 GitHub/Hugging Face 下载脚本；RadThinking 目前你手里的材料只是论文 PDF。
