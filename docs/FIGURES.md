# Figures

This repository includes PNG figures for README display and Mermaid diagrams for text-based rendering.

## Why there are three main README figures

The three README figures are intentionally different. They answer three different questions:

1. **Concept relationship** — what is the difference among model, CLI, tool, agent, and agent loop?
2. **Wrapper layer** — what was actually implemented as the current-stage engineering artifact?
3. **Workflow prototype** — how does the wrapper layer become a medical workflow / future agent-loop prototype?

## README figures

### Figure 1 — Relationship among Model, CLI, Tool, Agent, and Agent Loop

![Relationship among Model, CLI, Tool, Agent, and Agent Loop](../assets/concept_map_model_cli_tool_agent_loop.png)

### Figure 2 — CLI Wrapper Layer for Medical AI Tools

![CLI Wrapper Layer for Medical AI Tools](../assets/cli_based_ai_model_wrapper.png)

### Figure 3 — Medical Agent Loop Prototype

![Medical Agent Loop Prototype](../assets/medical_agent_loop_prototype.png)

## Mermaid diagrams

### Overall workflow prototype

```mermaid
flowchart TD
    U[User / Researcher] --> CLI[medai-cli JSON interface]
    CLI --> C[Controller / Workflow Orchestrator]
    C --> INF[Inference Backend<br/>TotalSegmentator or custom command]
    INF --> ADAPT[Adapter / Preparation]
    ADAPT --> SK[Optional ShapeKit Post-processing]
    SK --> QC[QC Checker]
    QC --> LV[Label Verifier / DSC Routing]
    LV --> VLM[VLM Label Expert<br/>Ollama qwen2.5vl or stub]
    VLM --> AM[AnnotationManager<br/>raw / predictions / updated]
    QC --> RT[RadThinking Trace]
    AM --> RQ[Human Review Queue]
    RT --> OUT[JSON outputs<br/>state / summary / traces]
    RQ --> OUT
```

### ScaleMAI-inspired mini EM loop

```mermaid
flowchart LR
    CT[CT image] --> PRED[Inference]
    PRED --> POST[Optional ShapeKit]
    POST --> VERIFY[Label Verifier<br/>DSC routing]
    VERIFY -->|accept| KEEP[Keep annotation]
    VERIFY -->|low DSC| VLM[VLM Label Expert]
    VERIFY -->|missing/empty| REPL[Replacement candidate]
    VLM --> DECIDE[Winner A/B/uncertain]
    DECIDE --> UPDATE[Annotation update<br/>AnnotationManager]
    UPDATE --> MSTEP[M-step stub<br/>training / data annealing plan]
    MSTEP --> NEXT[Next round]
```

### RadThinking-style trace

```mermaid
flowchart TD
    MASK[Mask + CT] --> OBS[Observation<br/>volume, bbox, centroid, HU]
    PREV[Prior mask] --> TEMP[Temporal comparison<br/>new/growing/stable/shrinking/resolved]
    REPORT[Report + clinical JSON] --> CONTEXT[Clinical context<br/>negation-aware parsing]
    PATHO[Pathology/follow-up JSON] --> CONC[Diagnostic conclusion field]
    OBS --> TRACE[Structured trace]
    TEMP --> TRACE
    CONTEXT --> TRACE
    CONC --> TRACE
```
