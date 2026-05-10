# medai-agent-loop-cli-anything

> **A CLI-Anything-style medical AI workflow prototype**  
> This repository shows how a medical AI capability can be packaged as a reproducible CLI tool, then organized into a lightweight medical agent-loop prototype.

This repository is a **research-engineering prototype**, **not** a clinical product and **not** a diagnostic system.  
Its purpose is to demonstrate the path from:

```text
single model / tool
→ CLI-callable wrapper
→ agent-callable commands
→ deterministic medical workflow prototype
→ future extensible medical agent loop
```

---

## 1. What the current task was

### 1.1 Teacher's requirement at this stage

My understanding of the task is:

> **The current goal is not to immediately build a complete medical agent.**  
> The goal is to first understand the relationship among **model, CLI, tool calling, agent, and agent loop**, and then implement a **minimal but real CLI-based AI/medical tool prototype** that can be demonstrated, explained, and extended later.

In practical terms, the teacher wanted to know whether I could:

1. explain the core concepts clearly;
2. study the provided papers / GitHub projects and understand how they relate;
3. build a runnable CLI demo;
4. show that the CLI can really call a model/tool and save outputs;
5. explain how this CLI layer can become one tool inside a later medical agent loop.

### 1.2 What I built

Based on that understanding, I built a prototype with two layers:

- **Layer A — wrapper layer**: a unified `medai-cli` interface that exposes medical AI functions as CLI commands;
- **Layer B — workflow layer**: a deterministic medical workflow prototype that chains those commands into a controlled loop.

So the current project is best described as:

```text
already implemented:
CLI wrapper layer + tool commands + deterministic workflow prototype

not yet implemented:
fully autonomous LLM-planning medical agent
```

This distinction is important. It keeps the project aligned with the current stage of the teacher's requirement.

---

## 2. How to read this repository: three figures, three questions

The three main figures in this README are intentionally **not repeating the same thing**.  
They answer **three different questions** that the teacher is likely to ask.

| Figure | Core question it answers | Why it exists |
|---|---|---|
| **Figure 1 — Concept relationship** | *What is the difference among model, CLI, tool, agent, and agent loop?* | Proves conceptual understanding. |
| **Figure 2 — CLI wrapper layer** | *What exactly did I implement this week as an engineering artifact?* | Proves the code is a real wrapper/tool system. |
| **Figure 3 — Medical workflow prototype** | *How does this wrapper layer grow into a medical agent-style workflow?* | Proves the project direction is correct and extensible. |

So the logic of this README is:

```text
first explain the concepts
→ then explain the implemented wrapper/tool layer
→ then explain the current medical workflow prototype
→ then show how the teacher-provided materials map into the code
→ then show how to run the demo
```

---

## 3. Figure 1 — Concept relationship

### Relationship among Model, CLI, Tool, Agent, and Agent Loop

![Relationship among Model, CLI, Tool, Agent, and Agent Loop](assets/concept_map_model_cli_tool_agent_loop.png)

### 3.1 What this figure is trying to show

This figure is the **concept map** of the whole project. It answers the question:

> **Before talking about the code, do I understand what these words actually mean and how they differ?**

The most important conceptual distinction is:

- a **model** is the backend capability;
- a **tool** is a callable function exposed to the outside;
- a **CLI** is the interface used to invoke tools reproducibly;
- an **agent** is the controller that decides what to call;
- an **agent loop** is the repeated control cycle: observe → decide → act → evaluate → repeat.

### 3.2 What each concept means in this repository

| Concept | Meaning in this project |
|---|---|
| **Model** | A backend capability such as TotalSegmentator, a custom command-line model, the included mock model, or the optional VLM through Ollama. |
| **Tool** | A callable function such as `infer`, `postprocess`, `label-verify`, `projection-build`, `vlm-label-expert`, `em-loop`, or `trace-build`. |
| **CLI** | The command-line entry point `medai-cli`, exposed through `run_medai_cli.py`, which lets a user or an upstream agent call the tools in a reproducible way. |
| **Agent** | The controller/orchestrator that selects the next tool or step according to the workflow policy. |
| **Agent Loop** | The repeated workflow of observe → infer / act → QC / verify → review / update → trace → save state. |
| **Outputs** | JSON files, logs, projection PNGs, annotation versions, traces, and review queues. |

### 3.3 Why this matters for the teacher's task

This figure establishes the conceptual foundation:

- I am **not** treating “agent” and “model” as the same thing;
- I understand that a model becomes more useful when wrapped as a **tool**;
- I understand that a tool becomes agent-callable when exposed through a **CLI** or tool registry;
- I understand that the **agent loop** is the orchestration logic above the tools.

In short, **Figure 1 proves conceptual understanding**.

---

## 4. Figure 2 — CLI wrapper layer

### CLI Wrapper Layer for Medical AI Tools

![CLI Wrapper Layer for Medical AI Tools](assets/cli_based_ai_model_wrapper.png)

### 4.1 What this figure is trying to show

This figure answers the engineering question:

> **What did I actually implement this week, in code?**

The answer is: I implemented a **CLI wrapper layer** that turns medical AI capabilities into structured commands.

This is the real engineering core of the current stage.

### 4.2 Wrapper flow

The wrapper layer follows this logic:

```text
command line input
→ parse arguments
→ load inputs
→ build runtime inputs / context
→ call model or tool backend
→ format outputs
→ save results and logs
```

### 4.3 What the wrapper already does

| Wrapper stage | What it means in general | What is implemented here |
|---|---|---|
| **Command line input** | user/agent provides a command | `python run_medai_cli.py --json <command> ...` |
| **Argument parser** | interpret flags and options | `click`-based command parser in `medai_cli.py` |
| **Input loader** | read the required files/folders | CT image, masks, reports, JSON metadata, patient folder |
| **Data builder** | build the right runtime input for the backend | organ lists, routing metadata, projection PNGs, clinical context |
| **Model / tool execution** | run the real backend | TotalSegmentator, ShapeKit wrapper, custom model command, mock model, optional VLM |
| **Output formatter** | convert results into structured artifacts | JSON serialization, state logging, trace generation, summary generation |
| **Result files** | persist results for demonstration/auditing | `final_summary.json`, `agent_state.json`, `patient_traces.json`, `review_queue.jsonl`, `annotation_versions/` |

### 4.4 Why this matters for the teacher's task

This figure is important because it shows that the project is **not just conceptual discussion**.

The wrapper layer already proves that:

- the code can be launched from the terminal;
- the CLI accepts explicit parameters;
- the program can read inputs;
- a backend model/tool can really be called;
- results are saved as structured outputs;
- the whole process is reproducible and demonstrable.

In short, **Figure 2 proves implementation of the current-stage deliverable**.

---

## 5. Figure 3 — Current medical workflow prototype

### Medical Agent Loop Prototype

![Medical Agent Loop Prototype](assets/medical_agent_loop_prototype.png)

### 5.1 What this figure is trying to show

This figure answers the system-design question:

> **How does the implemented wrapper layer become a medical workflow prototype, and how could it later support a fuller medical agent?**

So this figure is not just about one command. It is about how multiple tool calls are organized into a **controlled medical workflow**.

### 5.2 Current workflow logic

The implemented high-level workflow is:

```text
Medical inputs
→ Observe / Prepare
→ Infer
→ QC and Verification
→ Review / Refinement
→ Reasoning Trace
→ Save State and Outputs
```

The current implemented loop can be summarized as:

```text
Observe → Infer → QC → Verify → Review / Update → Trace → Save State
```

### 5.3 Why this is called a prototype instead of a full autonomous agent

The current workflow is **deterministic and auditable**, which is intentional.

This means:

- there is orchestration;
- there is looping / refinement;
- there are multiple tools;
- there is state recording;
- there is reasoning trace generation;
- but there is **not yet** a fully autonomous unconstrained LLM planner.

That is actually the correct scope for this stage.

### 5.4 How the current workflow maps to implemented modules

| Step | Implemented idea | Typical output |
|---|---|---|
| **Observe / Prepare** | patient-folder scan, input check, adapter, projection builder | normalized inputs / scan metadata |
| **Infer** | TotalSegmentator, custom backend, or mock model | segmentation masks or model outputs |
| **QC / Verify** | QC checker + Label Verifier | QC result, DSC routing decision |
| **Review / Update** | VLM Label Expert, human review queue, AnnotationManager, mini EM refinement | updated annotation candidate, decisions log |
| **Trace** | RadThinking-style structured trace generation | `patient_traces.json` |
| **Save State** | auditable state/event logging | `agent_state.json`, `final_summary.json` |

### 5.5 Why this matters for the teacher's task

This figure shows that the repository already answers the key design question:

- the wrapper layer is **not isolated**;
- it is already being used as part of a **medical workflow prototype**;
- the workflow is safe, auditable, and extensible;
- a future model, VLM, or training backend can be plugged in later.

In short, **Figure 3 proves the direction and architecture are aligned with the teacher's larger goal**.

---

## 6. What is implemented right now

The current repository already includes:

- a unified `medai-cli` entry point;
- AI inference through TotalSegmentator or a custom backend;
- optional ShapeKit post-processing wrapper;
- a Label Verifier based on Dice/DSC routing;
- mask-centered 2D projection image building;
- optional VLM Label Expert through Ollama `qwen2.5vl:7b` or stubbed backend;
- versioned annotation storage through `AnnotationManager`;
- a ScaleMAI-inspired **mini EM loop** with executable E-step and stubbed M-step;
- RadThinking-style longitudinal reasoning trace generation;
- auditable state logging and review queue output.

A concise project summary is:

```text
implemented now:
CLI wrapper layer + medical tool commands + deterministic workflow prototype

not implemented yet:
full model training loop, full human editing UI, autonomous LLM planner,
clinical diagnosis system
```

---

## 7. Teacher-provided materials and how they are used

A core part of the assignment was to study the provided materials and explain how they connect.  
The following table summarizes that relationship.

| Material / project | Core idea | Input | Output | Loop / tool idea | How it is reflected here |
|---|---|---|---|---|---|
| **CLI-Anything** | Expose software capability through CLI so that an agent can call it | existing function / software capability | command + logs / files / JSON | tool should be callable and reproducible | `medai-cli`, `--json`, `SKILL.md`, tool-oriented commands |
| **ScaleMAI** | Annotation refinement loop with verification and iteration | images, labels, predictions | refined annotations, routing decisions, training plan | E-step + M-step loop | Label Verifier, VLM Label Expert, AnnotationManager, mini EM loop |
| **ShapeKit** | Anatomy-aware mask correction | segmentation masks | refined masks | post-processing as a tool | optional `postprocess` wrapper |
| **PanTS** | Pancreatic CT segmentation / evaluation context | CT and reference labels | benchmark-style evaluation | dataset / evaluation workflow | PanTS import/eval helpers and scripts |
| **RadThinking** | Structured longitudinal medical reasoning | scans, masks, reports, clinical metadata | structured reasoning trace | observe temporal change + context integration | `radthinking.py`, trace-building commands and outputs |

### What I can explain from these materials

For each paper / GitHub project, I can now explain:

- **what the input is**;
- **what the output is**;
- **what tools/models it uses**;
- **what its loop structure is**;
- **what architecture idea I borrowed**;
- **where that idea appears in this repository**.

---

## 8. Repository structure

```text
medai-agent-loop-cli-anything/
├── README.md
├── QUICKSTART_WINDOWS.md
├── run_medai_cli.py
├── run_medai_cli.bat
├── assets/
├── agent-harness/
│   ├── setup.py
│   ├── requirements*.txt
│   ├── cli_anything/
│   │   └── medai/
│   │       ├── medai_cli.py
│   │       ├── skills/SKILL.md
│   │       └── core/
│   │           ├── agent_controller.py
│   │           ├── agent_state.py
│   │           ├── totalseg_runner.py
│   │           ├── shapekit_runner.py
│   │           ├── adapter.py
│   │           ├── label_verifier.py
│   │           ├── projection_builder.py
│   │           ├── vlm_label_expert.py
│   │           ├── annotation_manager.py
│   │           ├── em_loop.py
│   │           ├── radthinking.py
│   │           ├── qc_checker.py
│   │           ├── human_review.py
│   │           └── pants_utils.py
│   └── tests/
├── docs/
├── scripts/
├── examples/
└── third_party/
    └── mock_model/
```

---

## 9. Main CLI commands

| Command | Purpose |
|---|---|
| `doctor` | Check environment and backend availability |
| `infer` | Run AI segmentation backend or custom model command |
| `postprocess` | Run ShapeKit post-processing if available locally |
| `run` | One-shot infer + optional postprocess pipeline |
| `label-verify` | Compare annotation and prediction using DSC |
| `projection-build` | Generate mask-centered 2D projection PNGs |
| `vlm-label-expert` | Ask a VLM to compare candidate annotations |
| `em-loop` | Run the ScaleMAI-inspired mini EM loop |
| `agent-loop` | Run the patient-level medical workflow prototype |
| `trace-build` | Build one RadThinking-style trace |
| `pants-import-*` | Import PanTS-like cases into project layout |
| `pants-eval-case` | Compute a Dice sanity check for a case |

Typical command form:

```powershell
python run_medai_cli.py --json <command> ...
```

---

## 10. Label verification logic

The current project uses a conservative verification policy.

| Condition | Decision | Why |
|---|---|---|
| prediction missing | `review_queue` | nothing reliable to compare |
| current annotation missing | `auto_replace_candidate` | the prediction becomes a replacement **candidate**, not final truth |
| current annotation empty + prediction non-empty | `auto_replace_candidate` | likely missing label |
| both masks non-empty but DSC ≈ 0 | `send_to_vlm_label_expert` | likely localization disagreement; do not blindly overwrite |
| `0 < DSC < threshold` | `send_to_vlm_label_expert` | disagreement requires visual comparison |
| DSC ≥ threshold | `accept` | current annotation and prediction are sufficiently consistent |

This is intentionally safer than a naive rule such as:

```text
DSC = 0 → always replace
```

---

## 11. VLM Label Expert and mini EM loop

### 11.1 VLM Label Expert

The optional VLM Label Expert is used when automatic Dice-based verification is not sufficient.

Flow:

```text
CT image + annotation A + annotation B
→ build 2D projection overlays
→ send projections to VLM
→ parse JSON decision
→ update decision log or route to review queue
```

Typical output:

```json
{
  "winner": "A",
  "confidence": 0.80,
  "reason": "Candidate A is more anatomically plausible.",
  "num_projection_images_sent": 2
}
```

### 11.2 Mini EM loop

The mini EM loop is **inspired by ScaleMAI**, not a full reproduction.

```text
Round N
→ inference
→ optional postprocessing
→ E-step: verifier + optional VLM
→ annotation update
→ M-step: retraining stub / data annealing plan
→ metrics saved
```

#### Executable now

- inference;
- optional ShapeKit call;
- Dice-based verification;
- VLM routing;
- annotation versioning;
- decision logging;
- per-round metrics logging;
- dry-run-safe EM loop execution.

#### Still a stub / future work

- real model retraining;
- continual tuning backend;
- checkpoint generation;
- large-scale expert validation;
- full interactive human correction UI.

---

## 12. Installation

### 12.1 Minimal installation for the self-contained demo

This mode avoids private data and heavy external dependencies.

```powershell
conda create -n medai-agent python=3.10 -y
conda activate medai-agent
cd medai-agent-loop-cli-anything
pip install -r agent-harness\requirements.txt
pip install -e agent-harness
python run_medai_cli.py --json doctor
```

### 12.2 Optional TotalSegmentator support

```powershell
pip install -r agent-harness\requirements-totalseg.txt
```

### 12.3 Development tests

```powershell
pip install -r agent-harness\requirements-dev.txt
cd agent-harness
python -m pytest tests/ -v
```

For validation notes, see:

- `docs/VALIDATION_REPORT.md`
- `docs/VALIDATION_RUN_2026-05-10.md`

---

## 13. Self-contained demo for GitHub / meeting

This repository includes a self-contained demo that does **not** require private medical data.

### Step 1 — create synthetic demo data

```powershell
python scripts\create_radthinking_demo.py
```

### Step 2 — check the generated patient folder

```powershell
python run_medai_cli.py --json radthinking-check `
  --patient-folder data\radthinking_demo\patient_001
```

### Step 3 — run the workflow prototype

```powershell
python run_medai_cli.py --json agent-loop `
  --patient-folder data\radthinking_demo\patient_001 `
  --output-folder outputs\agent_loop_mock_self_contained `
  --backend custom `
  --model-command "python third_party\mock_model\mock_seg_infer.py --image {image} --output {output}" `
  --postprocess none `
  --organ liver `
  --expected-organs liver
```

### Step 4 — inspect the outputs

```text
outputs/agent_loop_mock_self_contained/
├── agent_state.json
├── final_summary.json
├── patient_traces.json
├── review_queue.jsonl
└── scan_outputs/
```

This demonstration is important because it proves:

- the CLI really runs;
- a backend model/tool is really called;
- outputs are really saved;
- the project is not only conceptual, but executable.

---

## 14. Recommended 10-minute meeting demo

Suggested structure:

| Time | Content |
|---:|---|
| 1 min | What I understood the task to be |
| 2 min | What I learned from the papers / GitHub projects |
| 2 min | Explain Figure 1: concept relationship |
| 2 min | Explain Figure 2: wrapper layer |
| 1 min | Explain Figure 3: workflow prototype |
| 2 min | Run CLI demo and show outputs |

Recommended live commands:

```powershell
python run_medai_cli.py --json doctor
python scripts\create_radthinking_demo.py
python run_medai_cli.py --json radthinking-check --patient-folder data\radthinking_demo\patient_001
python run_medai_cli.py --json agent-loop `
  --patient-folder data\radthinking_demo\patient_001 `
  --output-folder outputs\meeting_demo `
  --backend custom `
  --model-command "python third_party\mock_model\mock_seg_infer.py --image {image} --output {output}" `
  --postprocess none `
  --organ liver `
  --expected-organs liver
```

Then show:

```text
outputs/meeting_demo/final_summary.json
outputs/meeting_demo/agent_state.json
outputs/meeting_demo/patient_traces.json
outputs/meeting_demo/review_queue.jsonl
```

For static examples, also see:

```text
examples/sample_outputs/
```

---

## 15. Output artifacts

| Output | Meaning |
|---|---|
| `final_summary.json` | final pipeline-level summary |
| `agent_state.json` | auditable event trajectory, one event per step |
| `patient_traces.json` | RadThinking-style reasoning traces |
| `review_queue.jsonl` | cases requiring VLM or human review |
| `annotation_versions/` | raw/prediction/updated annotations and decisions |
| `rounds_metrics.json` | mini EM loop per-round metrics |
| projection PNGs | human/VLM-readable overlay images for comparison |

Example sample outputs are stored under:

```text
examples/sample_outputs/
```

---

## 16. What is intentionally not included in GitHub

This upload intentionally excludes:

```text
real CT data
real PanTS data
runtime outputs
ShapeKit source code
PanTS source repository
teacher-provided private files
paper PDFs
model weights
API keys / tokens / secrets
```

Why:

- to avoid uploading medical or derived data;
- to avoid third-party copyright / license problems;
- to avoid publishing teacher-provided or unpublished material;
- to keep the GitHub repository lightweight and reproducible.

Related notes:

- `UPLOAD_MANIFEST.md`
- `PACKAGE_NOTES.md`
- `third_party/README.md`

---

## 17. Current limitations

The project should currently be described as follows:

| Topic | Current status |
|---|---|
| Full ScaleMAI reproduction | **No**; only a mini EM-inspired prototype |
| Real training backend / continual tuning | **Not yet**; M-step is a stub |
| Full autonomous LLM planner | **Not yet**; current workflow is deterministic |
| Clinical diagnosis | **No**; not a diagnostic system |
| Real PanTS tumor model | **Not bundled**; can be plugged in through a custom backend |
| ShapeKit source | **Not bundled**; local installation required if used |
| Optional VLM | **Supported**, but requires local Ollama model |

A precise summary sentence is:

> **Current status = wrapper layer + tool commands + deterministic medical workflow prototype.**  
> **Not yet = full autonomous medical agent with full training/retraining stack.**

---

## 18. Next steps

The most natural next steps are:

1. plug in a task-specific or lab-provided segmentation model through `--backend custom`;
2. add a real training backend for the M-step;
3. connect human review/editing to the annotation refinement path;
4. expand the VLM Label Expert evaluation;
5. add report-to-structure extraction for richer RadThinking-style clinical context;
6. optionally add a constrained LLM planner, while keeping a strict tool registry and JSON action schema for safety.

---

## 19. Suggested verbal explanation for the teacher

A concise explanation that matches the current repository is:

```text
This week, I focused on understanding the relationship among model, CLI,
tool calling, agent, and agent loop. My understanding is that the current
stage is not to build a full medical diagnosis agent immediately, but first
to implement a minimal, real CLI wrapper around medical AI capabilities.

Based on that, I built a CLI-Anything-style medical AI wrapper layer. The
CLI can parse arguments, read CT images or patient folders, call a model or
tool backend, and save structured outputs such as JSON summaries, state logs,
traces, and review artifacts.

On top of that wrapper layer, I implemented a deterministic medical workflow
prototype that includes inference, QC, label verification, optional VLM
comparison, annotation management, a mini EM-inspired refinement loop, and
RadThinking-style trace generation.

So the current repository already shows a runnable wrapper layer and an
extensible workflow prototype. The next step would be to plug in more
medical models and, if needed, later add a more autonomous planner.
```

---

## 20. Final takeaway

If the teacher reads only one paragraph, the key message is:

> This repository demonstrates that I understood the conceptual relationship among **model, tool, CLI, agent, and agent loop**; I studied the provided papers/projects and mapped them into a coherent design; I implemented a **real CLI wrapper layer** for medical AI tools; and I extended it into a **deterministic medical workflow prototype** with verification, refinement, trace generation, and auditable outputs. The current stage is therefore complete as a **CLI-based medical AI prototype**, while still leaving room for future expansion into a fuller medical agent.

