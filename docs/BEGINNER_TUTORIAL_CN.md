# 初学者教程

## 你要先理解的核心

AI 模型不只包括 GPT/Claude/Qwen。TotalSegmentator 是医学图像分割 AI 模型/工具，输入 CT，输出器官 mask。ShapeKit 不是模型，是后处理工具。CLI-Anything 不是模型，是封装标准。

## 为什么要 CLI

agent 要自动调用工具。如果一个工具要 `python main.py`，另一个要 API，另一个要 TensorFlow 命令，agent 就很难统一管理。所以我们把每个工具都封装成统一命令：

```bash
medai-cli infer ...
medai-cli postprocess ...
medai-cli agent-loop ...
```

每个命令都输出 JSON，agent 就能读懂状态。

## 最小运行流程

1. 安装环境。
2. 生成 demo patient。
3. 用 mock model 跑 agent-loop。
4. 查看 `agent_state.json` 和 `review_queue.jsonl`。
5. 再换成真实 TotalSegmentator。

## 文件结构

```text
agent-harness/cli_anything/medai/medai_cli.py   # 命令入口
agent-harness/cli_anything/medai/core/          # 核心逻辑
third_party/ShapeKit-main/                      # 本地可选 ShapeKit
third_party/PanTS-main/                         # 本地可选 PanTS
third_party/CLI-Anything-reference/             # CLI-Anything 参考
scripts/create_radthinking_demo.py              # 生成测试数据
```

## 为什么这样组织

- `medai_cli.py` 负责命令入口。
- `core/totalseg_runner.py` 负责调用 AI model。
- `core/shapekit_runner.py` 负责调用 ShapeKit，并自动安全配置 target_organs。
- `core/radthinking.py` 负责四步 reasoning trace。
- `core/agent_controller.py` 负责 loop controller。
- `skills/SKILL.md` 告诉 agent 这个工具怎么用。
