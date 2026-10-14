# PRATYAKSH (PUGMARK)
### *Content-First Data Leak Provenance & Forensic Custody Reconstruction*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/React-18.x-61DAFB.svg?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6.svg?logo=typescript)](https://www.typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.x-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![INNOVATHON 2026](https://img.shields.io/badge/INNOVATHON-2026%20Cybersecurity-red.svg)](#)

---

## 📌 Executive Summary

When sensitive company records surface in unexpected locations—such as a dark web forum, a file-sharing dump, or a Telegram channel—forensic investigators face a critical bottleneck: **event logs are noisy, fragmented, and incomplete**. Traditional Security Information and Event Management (SIEM) solutions query existing logs, but fail when an insider bypasses endpoint monitoring, when attackers suppress auditing, or when intermediate tools launder the data format.

**PRATYAKSH** (*Sanskrit: directly evident, verifiable proof* / developed under codename **PUGMARK**) addresses **Problem Statement #18 (Cybersecurity: Tracing a Data Leak Across Systems)** for **INNOVATHON 2026**.

Instead of merely searching logs, PRATYAKSH starts from the **leaked content itself**. Using **zero-raw-data privacy-preserving MinHash sketches**, temporal watermarks, and format fingerprints, PRATYAKSH matches the leaked records back to known export artifacts. It then traverses the provenance graph using an **explicit, penalized missing-hop inference model**, ranking candidate custody paths, evaluating actor behavioral anomalies, and computing actionable containment chokepoints.

```
       +-----------------------------------------------------------+
       |   Leaked Sample Discovered (e.g. Mock Telegram Channel)   |
       +-----------------------------+-----------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |        Privacy-Preserving Fingerprinting & Sketching      |
       |  - HMAC-SHA256 Bottom-k MinHash Sketches (Normalized IDs) |
       |  - Format Profile (Date/Phone style, quoting, delimiters) |
       |  - Record Watermarking (Newest creation timestamp)        |
       +-----------------------------+-----------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |                 Candidate Origin Ranking                  |
       |  - Hard Constraints (Schema completeness, Watermark gap)  |
       |  - Soft Scoring: Jaccard Containment, Specificity, Style  |
       +-----------------------------+-----------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |             Custody Path Search & Inference               |
       |  - Observed Movement Edges (Download, Copy, Send, API)    |
       |  - Penalized Hidden/Missing Hops (Unlogged endpoints)     |
       |  - Empirical Loss Estimation from Sequence-Number Gaps    |
       +-----------------------------+-----------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |        Actor Anomaly Scoring & Hypothesis Ranking         |
       |  - 30-Day Log-Normal Volume Baselines (Z-score)           |
       |  - Off-Hours, First-Time Action & Privilege Shifts        |
       |  - Softmax Relative Likelihood over Plausible Paths       |
       +-----------------------------+-----------------------------+
                                     |
                                     v
       +-----------------------------------------------------------+
       |           Actionable Containment & Forensics              |
       |  - Greedy Chokepoint Recommendations (Max Path Mass)      |
       |  - Information-Theoretic Missing Evidence Requests        |
       |  - Masked Previews, Audited Justified Reveals & Reports   |
       +-----------------------------------------------------------+
```

---

## 🎯 The Core Problem & The PRATYAKSH Advantage

> *"Sensitive information appears in an unexpected location, but several services, users, and data transfers may be involved. Investigators need to narrow down possible causes from incomplete event records without exposing more data."* — **Problem Statement #18**

| Problem Requirement | Traditional SIEM / Log Analysis | PRATYAKSH Approach |
|---|---|---|
| **Starting Point** | Keyword searches on existing event logs. Fails if egress wasn't logged. | **Content-First**: Fingerprints the leaked file and pinpoints exact originating export. |
| **Incomplete Logs** | "No log, no event." The investigation hits a dead end. | **Inferred Custody Paths**: Graph search introduces explicit, penalized hidden hops. |
| **Privacy Preservation** | Centralized log ingestion often duplicates and exposes raw PII. | **Zero-Raw-Data Sketches**: Compares keyed 64-bit HMAC sketches; raw records never cross boundaries. |
| **Data Masking** | Static masking or unrestricted analyst access. | **Masked by Default + Audited Reveal**: Mandatory cryptographic masking; reveals require logged justification. |
| **Containment Guidance** | Generic advice ("reset passwords"). | **Greedy Chokepoints**: Calculates exact permission/channel closure covering maximum path likelihood. |
| **Forensic Uncertainty** | Binary assumptions or fabricated confidence. | **Relative Likelihood & Evidence Entropy**: Recommends which log source would maximize information gain. |

---

## 🔬 Mathematical & Algorithmic Foundations

### 1. Keyed Bottom-$k$ MinHash Containment
Raw records are never ingested by the tracing engine. Each candidate dataset export $E$ and the leaked file $L$ compute a bottom-$k$ sketch ($k = 512$) on normalized identifier columns (`customer_id`, `email`, `phone`, `policy_no`):

$$\text{hash}(x) = \text{HMAC-SHA256}(K_{\text{case}}, \text{normalize}(x))[:8]$$

The Jaccard similarity $J$ between the smallest $k$ hash values of $L$ and $E$ estimates the true set containment $C$:

$$C(L \subseteq E) = \frac{J \cdot (|L| + |E|)}{(1 + J) \cdot |L|}$$

### 2. Candidate Origin Scoring
Surviving candidate exports that pass hard constraints (containing all leaked columns and created on or before leak discovery) are scored via:

$$\text{origin\_fit}(E) = 5.0 \cdot \ln(\max(C, 0.001)) + 1.0 \cdot \ln\left(\text{clip}\left(\frac{|L|}{|E|}, 0.01, 1\right)\right) + 2.0 \cdot \text{format\_sim}(L, E) + \text{WM}(E)$$

* **Specificity ($\frac{|L|}{|E|}$)**: Penalizes sprawling, massive database dumps when a targeted subset export explains the leak.
* **Format Similarity**: Compares delimiters, quoting rules, header casings, null tokens, and phone/date formatting dialect to detect intermediate tool manipulation.
* **Watermark Penalty ($\text{WM}$)**: If the leak represents $\ge 90\%$ of an export, but the export was created hours after the newest record timestamp in the leak, it is penalized for missing fresh records:
  $$\text{WM}(E) = -\text{arrivals\_per\_hour} \times \Delta t_{\text{gap}}$$

### 3. Custody Graph Traversal with Penalized Hidden Hops
Custody graphs model data transitions across systems (`sys:`), employee endpoints (`ep:`), and external locations (`ext:`). To bridge missing log intervals:

$$\text{path\_cost} = \sum_{\text{hop} \in \text{path}} c(\text{hop})$$

$$c(\text{hop}) = \begin{cases} 
0.10 & \text{if observed in telemetry} \\
0.50 & \text{if hidden from an unmonitored employee endpoint} \\
-\ln(p_{\text{loss\_source}}) + 1.0 & \text{if hidden from an enterprise logged source}
\end{cases}$$

Empirical source loss rate $p_{\text{loss\_source}}$ is computed in real time from sequence number gaps ($\text{seq}$ assigned prior to log drops).

### 4. Actor Anomaly & Relative Likelihood
Actor activity is evaluated against a 30-day log-normal behavioral baseline:

$$z = \frac{\ln(1 + \text{rows}) - \mu_{\text{actor}}}{\sigma_{\text{actor}}}$$
$$\text{anomaly} = \min(z, 4.0) + 0.5 \cdot \mathbf{1}_{\text{off\_hours}} + 0.7 \cdot \mathbf{1}_{\text{first\_time}} + 0.7 \cdot \mathbf{1}_{\text{recent\_privilege\_shift}}$$

Hypotheses are ranked using relative likelihood with temperature scaling ($T = 1.0$):

$$S(\text{path}) = 1.0 \cdot \text{origin\_fit} - 1.0 \cdot \text{path\_cost} + 0.6 \sum_{a \in \text{actors}} \text{anomaly}(a)$$
$$P(\text{path}) = \frac{e^{S(\text{path}) / T}}{\sum_{p'} e^{S(p') / T}}$$

---

## 🏛 System Architecture

```
                          ┌───────────────────────────────────────────────┐
                          │               REACT FRONTEND                  │
                          │   Cytoscape Graph • Recharts • Dark Theme     │
                          └───────────────▲───────────────────────────────┘
                                          │ HTTP / JSON
                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FASTAPI BACKEND & PRIVACY LAYER                  │
│                                                                         │
│   • /api/scenario/generate   • /api/trace          • /api/reveal        │
│   • /api/leak/export         • /api/canary/alert   • /api/benchmark     │
│                                                                         │
│   ┌───────────────────────────┐      ┌──────────────────────────────┐   │
│   │   PRIVACY & AUDIT LAYER   │      │       INCIDENT REPORTING     │   │
│   │  - Cryptographic Masking  │      │  - DPDP Compliance Brief     │   │
│   │  - Audited Reveal Engine  │      │  - HTML Incident Dossier     │   │
│   └─────────────▲─────────────┘      └──────────────────────────────┘   │
└─────────────────┼───────────────────────────────────────────────────────┘
                  │
      ┌───────────┴───────────────────────────────┐
      │                                           │
      ▼ (Public Scenario Only)                    ▼ (Isolated Benchmark/Test)
┌───────────────────────────┐       ┌─────────────────────────────────────┐
│       TRACING ENGINE      │       │          SYNTHETIC SIMULATOR        │
│                           │       │                                     │
│  - Canary Pinning         │       │  - Nova Health 30-Day Activity      │
│  - Sketch Containment     │       │  - Archetypes (A1 to A5)            │
│  - Missing-Hop Search     │       │  - Configurable Log-Loss (0 to 60%) │
│  - Behavioral Anomaly     │       │  - Mock Telegram Discovery Channel  │
│  - Greedy Chokepoints     │       │  - Ground Truth Separation          │
│  - Evidence Entropy       │       │                                     │
└───────────────────────────┘       └─────────────────────────────────────┘
```

---

## 📂 Repository Structure

```
PRATYAKSH/
├── README.md                           # Master project documentation
├── docs/                               # Engineering specifications & data contracts
│   ├── 00_PROJECT_CONTEXT.md           # Problem breakdown, story (seed 42), principles
│   ├── 01_DATA_CONTRACT.md             # Frozen TypeScript/Pydantic schemas & constants
│   ├── 02_SIMULATOR.md                 # Simulator spec, archetypes, loss & discovery
│   ├── 03_ENGINE.md                    # Algorithmic engine spec, stages, formulas
│   ├── 04_TEST_PLAN.md                 # Hand-crafted scenarios (H1-H8), test suites
│   ├── 05_PHASES.md                    # Phased execution plan & quality gates
│   ├── 06_WORK_SPLIT.md                # Roles, ownership, load-shedding hierarchy
│   ├── FEATURES.md                     # Locked feature catalog & demo steps
│   ├── FRONTEND.md                     # UI component hierarchy & interaction states
│   ├── UI_UX_DESIGN.md                 # Investigative design tokens & layout guidelines
│   └── MASTER_PROMPT.MD                # Autonomous agent orchestration instructions
├── backend/                            # Python 3.11+ Backend Services
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point & API routes
│   │   ├── config.py                   # Centralized hyperparameter weights & tolerances
│   │   ├── models.py                   # Pydantic v2 mirrors of 01_DATA_CONTRACT.md
│   │   ├── common/
│   │   │   └── sketch.py               # Shared HMAC bottom-k MinHash & Jaccard logic
│   │   ├── sim/                        # Synthetic company generator & loss modeling
│   │   ├── engine/                     # Provenance graph, anomaly, ranking & chokepoints
│   │   ├── privacy/                    # Masking filters & immutable audit logger
│   │   ├── report/                     # Automated incident report generator
│   │   └── bench/                      # Benchmark harness against naive baselines
│   ├── tests/                          # Automated Pytest suite (H1 to H8 scenarios)
│   └── scripts/
│       ├── validate.py                 # Contract validation tool
│       └── make_demo_bundle.py         # Offline replay bundle generator (demo.json)
└── frontend/                           # React + Vite + Tailwind Forensic Console
    ├── src/
    │   ├── components/                 # Graph (Cytoscape), Incident, Hypotheses, Tabs
    │   ├── types/contract.ts           # TypeScript interfaces mirrored from data contract
    │   └── App.tsx                     # Main forensic single-page dashboard
    └── public/
        └── demo.json                   # Standalone offline replay bundle for live demos
```

---

## ⚡ Quickstart Guide

### Prerequisites
* **Python**: 3.11 or newer
* **Node.js**: v20.x or newer
* **npm**: v10.x or newer

---

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/Tanish18906/PRATYAKSH.git
cd PRATYAKSH

# Create and activate a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Run test suite to verify math and contract integrity
pytest -q

# Start the FastAPI backend server (port 8000)
uvicorn app.main:app --port 8000 --reload
```

Verify backend health:
```bash
curl http://localhost:8000/api/health
# Returns: {"status":"ok","contract_version":"1.0","engine_version":"1.0.0"}
```

Trace one of the built-in hand-written test scenarios (`scn:H1` to `scn:H8`, loaded automatically until the simulator is available):
```bash
curl http://localhost:8000/api/scenario/scn:H1
curl -X POST http://localhost:8000/api/leak/export -H 'content-type: application/json' -d '{"scenario_id":"scn:H1","message_id":1}'
curl -X POST http://localhost:8000/api/trace -H 'content-type: application/json' -d '{"scenario_id":"scn:H1"}'
```
All data is SIMULATED. Every export and trace appends one line to `backend/data/audit.jsonl`.

---

### 2. Frontend Setup

In a separate terminal:
```bash
cd frontend

# Install Node dependencies
npm install

# Start the local development server
npm run dev
```

Open your browser at `http://localhost:5173`.

---

### 3. 100% Offline Replay Mode
PRATYAKSH is engineered to function completely offline without internet connectivity. If the backend is not running, the frontend automatically falls back to `public/demo.json` (precomputed Seed 42 forensic trace) and displays an **OFFLINE REPLAY** indicator.

To regenerate the offline bundle:
```bash
python backend/scripts/make_demo_bundle.py
```

---

## 🎭 The Demo Walkthrough (Seed 42 / Archetype A1)

PRATYAKSH ships with a baseline ground-truth demonstration scenario (**Seed 42, Nova Health**):

```
+---------------------------------------------------------------------------------------+
| 2026-10-09 02:10 UTC : etl-nightly generates Export E1 (48,900 rows, ISO format)      |
| 2026-10-09 21:40 UTC : Analyst Ravi Menon downloads E1 to laptop (normal: 300 rows)   |
| 2026-10-10 02:10 UTC : etl-nightly generates Decoy E4 (same filter, 400 newer rows)  |
| 2026-10-10 22:00 UTC : [LOG DROPPED] Ravi uploads CSV to Telegram channel             |
| 2026-10-12 08:30 UTC : Leak found on mock Telegram channel (48,212 rows)              |
+---------------------------------------------------------------------------------------+
```

### Forensic Steps in the Dashboard:
1. **Discovery (Simulated Telegram)**: Open the simulated Telegram tab, locate the leaked CSV attachment `nova_customers_cg.csv`, and click **Export & Trace**.
2. **Fingerprint & Origin Match**:
   * **E1 (Nightly Export)** ranks as Top Origin ($\approx 95\%$ containment, exact format match).
   * **E2 (Contractor Arjun's Dump)** is excluded by the **watermark rule** (created before the newest record in the leak existed).
   * **E4 (Decoy Next-Night Export)** is downranked due to the **watermark gap penalty** (the leak lacks E4's 400 new arrivals).
3. **Provenance Graph Navigation**:
   * Solid edges indicate observed database and warehouse downloads.
   * A **dashed amber animated edge** illustrates the inferred missing hop from Ravi Menon's laptop to Telegram (`est. loss 40%`).
4. **Behavioral Anomaly & Ranking**:
   * Ravi Menon's download shows an anomaly score of $z > 3.8$ (downloaded 48,900 rows vs. standard 300-row baseline) combined with off-hours activity (21:40 UTC).
5. **Actionable Containment (Chokepoint)**:
   * Recommends revoking Ravi Menon's bulk export entitlement on `sys:bi-warehouse`, neutralizing over $78\%$ of plausible leak paths.
6. **Information-Theoretic Evidence Suggestion**:
   * Pinpoints that requesting **proxy/endpoint egress logs for Ravi's laptop between Oct 9–10** resolves the greatest entropy gap.
7. **Privacy-Preserving Reveal**:
   * Inspect masked records (`r***@example.com`, `+91-98******21`). Click **Reveal Value**, input justification (*"Verify high-risk VIP breach notice"*), and confirm audit trail logging.

---

## 📊 Benchmark & Empirical Evaluation

PRATYAKSH evaluates performance against three traditional industry baselines across varying degrees of simulated log-loss ($0\%$, $20\%$, $40\%$, $60\%$):

* **B1 (Last Accessor)**: Attributed to the entity with the most recent read timestamp on candidate tables.
* **B2 (Biggest Exporter)**: Attributed to the user or service account with the highest gross export volume.
* **B3 & B4**: Baseline origin models using largest or most recent export timestamps.

> **Status: no benchmark has been run yet.** No accuracy figure is claimed here. When the benchmark runner exists,
> results will be produced on seeds 50 to 199 (tuning uses seeds 0 to 49 only) and reported as measured on
> **synthetic data from our own simulator**, not as real-world accuracy.

---

## 🛡 Security & Privacy Guardrails

* **Hash-Only Matching**: The engine compares keyed sketches and schema metadata, never raw rows.
* **Cryptographic Salting**: HMAC keys are randomized per case scenario, neutralizing rainbow table attacks on lower-entropy identifiers (e.g. phone numbers).
* **Immutability & Accountability**: All data unmasking, report downloads, and trace executions write structured events to `backend/data/audit.jsonl`.
* **Honest Limitations**:
  * Output represents **relative likelihood**, never definitive judicial verdict.
  * Real-world web scraping/crawler evasion is out of scope; detection is synthetic.
  * Data leakage via non-digital avenues (physical screens, photos) cannot be tracked.

---

## 👥 Authors & Acknowledgments

* **Tanish Mishra** ([@Tanish18906](https://github.com/Tanish18906)) — Tracing Engine, Privacy Layer, API & Math Foundations.
* **Anmol** — Synthetic Data Simulator, Mock Discovery UI & Benchmark Evaluation.

*Developed with pride for **INNOVATHON 2026** (Problem Statement #18: Tracing a Data Leak Across Systems).*

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
