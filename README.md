# Enterprise AI Customer Support Triage & Observability Engine

> **Phase 2 Final Project** | The Knowledge House AI Business Solutions Engineering Fellowship  
> **Logging & Observability Engineer:** Nataki Boykin  
> **Consultancy Team:** Come On Back AI Systems Consultancy (Enrique Quezada, Lance Gonzalez, Mitchy Derose, Julian Seiferth, Nataki Boykin)

---

## 1. Project & Problem Statement

**The Challenge:** Northstar Support Co. relies on a manual team of 6 human agents who read, tag, look up corporate policies, and draft customer support responses. While quality and trust are high, queue throughput creates an average resolution SLA of **18 hours** per ticket.

**The Solution:** We engineered a production-grade, multi-agent control system that automates intent triage, vector policy retrieval, draft synthesis, and QA auditing. Routine tickets auto-dispatch in **~20 seconds**, while high-risk edge cases route to a Streamlit Human-in-the-Loop review queue—reducing overall handling costs from **$137,000 to $15,500/year**.

---

## 2. My Individual Technical Contribution

As the **Logging & Observability Engineer (The Chief Inspector)**, I was directly responsible for designing, building, and maintaining three core components of the system:

### Key Deliverables & Codebase Ownership

* **Agent Intent & Priority Classification (`agents/triage.py`):**
  * Designed the intent classification logic using LangChain structured outputs (`with_structured_output()`) to parse incoming ticket text into category (Billing, Technical, Returns), urgency priority (P1–P4), and initial confidence levels.

* **Lifecycle Telemetry & Event Logging (`logging_utils.py`):**
  * Built the structured event-logging pipeline that captures every state transition, vector retrieval call, draft revision, and Critic decision to immutable JSONL audit streams (`logs/run_<timestamp>.jsonl`).

* **Human-in-the-Loop Review CLI & Queue (`approval_queue.py`):**
  * Implemented the underlying exception queue state manager (`approval_queue.json`) that isolates flagged or rejected drafts for supervisor inspection, enabling inline modifications and one-click dispatch.

* **Written Architectural Deliverable:**
  * Authored *"What We Keep From The Old Process"*—a policy analysis detailing how human supervisor oversight, brand tone standards, and escalation rules were preserved within our automated architecture.

---

## 3. Architecture & Technical Approach

System execution is governed by plain Python control flow to guarantee explicit control over agent state transitions and approval gates.

```text
[ tickets.csv ]
      |
      v
[ TRIAGE AGENT ] ----> (Nataki: extracts category, priority, confidence)
      |
      v
[ POLICY LOOKUP ] ---> (Lance: vector search over policy knowledge base)
      |
      v
[ DRAFTER AGENT ] <--- (Mitchy: synthesizes grounded draft)
      |           ^
      |           | (Revision notes; max 2 retries)
      v           |
[ CRITIC AGENT ] ----- (Julian: audits safety, tone & policy rules)
      |
      v
[ APPROVAL GATE ]
      +-- Approved & Unflagged ---> Auto-Sent (~20s SLA)
      +-- Flagged / Max Retries --> [ approval_queue.json ] ---> (Nataki: Human Review)
```

---

## 4. Tools & Technologies Used

* **Language & Frameworks:** Python 3.10+, Streamlit (Dashboard UI), LangChain (Structured LLM Outputs).
* **Observability & Storage:** Custom JSONL Event Logging, Structured JSON Queue State Management.
* **Testing & CLI:** Python Mock Engine (`--mock`), Terminal Review Loop (`approval_queue.py`).

---

## 5. Results & Business Impact

| Metric | Manual Baseline | Multi-Agent System | Net Impact |
| :--- | :--- | :--- | :--- |
| **Handling Cost / Ticket** | $5.50 | **~$0.62** | **~$4.88 Savings / Ticket** |
| **Annual Handling Cost** | ~$137,000 | **~$15,500** | **~$121,500 Annual Savings** |
| **Resolution SLA (Auto-Send)** | 18 Hours | **~20 Seconds** | **~99% Speed Improvement** |
| **Blended SLA (All Tickets)** | 18 Hours | **<=1.4 Hours** | **~92% Throughput Increase** |

---

## 6. Quick Start & Local Execution

### 1. Clone & Setup Environment
```bash
git clone https://github.com/NatakiSystems/ai-triage-observability-engine.git
cd ai-triage-observability-engine
pip install -r requirements.txt
```

### 2. Run Mock Benchmark (Zero API Cost)
```bash
python main.py --mock
```

### 3. Launch Observability Dashboard & Review Queue
```bash
streamlit run streamlit_app.py
```

---

## 7. Engineering Team Roster

* **Orchestrator Engineer:** Enrique Quezada (`orchestrator.py`, `main.py`)
* **Integration Engineer:** Lance Gonzalez (`tools/policy_lookup.py`, `tickets.csv`)
* **Prompt Engineer:** Mitchy Derose (`prompts/drafter.md`, `agents/drafter.py`)
* **QA / Critic Engineer:** Julian Seifurth (`agents/critic.py`, `prompts/critic.md`)
* **Logging & Observability Engineer:** Nataki Boykin (`agents/triage.py`, `logging_utils.py`, `approval_queue.py, streamlit_app.py`)

---

---

### 8. Live Observability & Governance Console

The system features an enterprise-grade **Streamlit Governance & Observability Console** enabling real-time monitoring of multi-agent operations, full audit trail telemetry, and Human-in-the-Loop (HITL) exception management.

**Key Capabilities**

* **Live Governance KPIs:** Real-time visibility into overall ticket throughput, automation rates (auto-dispatch vs. flagged escalations), average latency per ticket, and pending supervisor review queues.
* **Immutable Flight Recorder & Audit Trail:** Detailed timeline inspection of structured JSONL event logs showing every agent state transition: triage classification, dynamic policy retrieval tool calls, multi-turn draft generation, and Critic QA audits.
* **Supervisor Exception Inbox (`approval_queue.json`):** Dedicated human checkpoint interface isolating policy violations, low-confidence attempts, and legal triggers—enabling inline supervisor edits, rejections, or one-click approval dispatches.

```bash
# Launch the dashboard locally
streamlit run streamlit_app.py

> **Live Demo:** Access the hosted dashboard at `https://<your-streamlit-app-url>.streamlit.app`
