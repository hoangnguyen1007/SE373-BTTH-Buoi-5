# Agent Tools & Skills Lab - SE373

A robust implementation of tool calling, dynamic skill orchestration, and data validation pipelines for AI Agents (Lab 05, Course SE373 - UIT).

---

## Directory Structure

```text
.
├── block-1/                                # Block 1: Policy Lookup by Version
│   ├── agent.py                            # Agent graph configured with list_files & refund-policy skill
│   ├── tools/
│   │   ├── files.py                        # list_files tool with workspace path isolation
│   │   └── __init__.py
│   ├── skills/refund-policy/
│   │   ├── SKILL.md                        # Dynamic discovery, purchase-date matching, disambiguation prompt
│   │   └── references/answer-template.md   # Standardized Markdown response template
│   ├── data/policies/                      # Versioned policy documents
│   │   ├── policy-before-oct.md            # Effective prior to Oct 1, 2026
│   │   └── policy-from-oct.md              # Effective from Oct 1, 2026 onwards
│   ├── traces/                             # Execution traces (JSONL format)
│   │   ├── case_a_purchase_before_oct.jsonl
│   │   ├── case_b_purchase_from_oct_renamed.jsonl
│   │   └── case_missing_activation_info.jsonl
│   └── analysis.md                         # Technical analysis and trade-off evaluation
│
├── block-2/                                # Block 2: Workload & Overload Verification
│   ├── skills/csv-quality/
│   │   ├── scripts/check_csv.py            # CSV validator: --max-hours, deduplication, hours_by_owner
│   │   ├── SKILL.md                        # Skill definition enforcing threshold prompt & bash execution
│   │   └── references/report-template.md   # Report schema containing summary, overloads, and excluded rows
│   ├── data/
│   │   ├── workload.csv                    # Standard test dataset (6 records)
│   │   └── workload-edge.csv               # Edge-case dataset (invalid hours on first occurrence)
│   ├── tests/
│   │   └── test_check_csv.py               # Automated pytest suite (17 test cases, 100% passing)
│   ├── output/                             # Script and agent artifacts
│   │   ├── workload_8.json                 # Direct JSON output (threshold = 8.0h)
│   │   ├── workload_9.json                 # Direct JSON output (threshold = 9.0h)
│   │   ├── workload_edge.json              # Direct JSON output (edge case, threshold = 0.0h)
│   │   └── workload.md                     # Agent-generated report following report-template.md
│   ├── traces/                             # Execution traces (JSONL format)
│   │   ├── trace_workload_threshold_8.jsonl
│   │   ├── trace_workload_threshold_9.jsonl
│   │   ├── trace_missing_threshold.jsonl
│   │   └── trace_missing_file.jsonl
│   └── analysis.md                         # Technical analysis on script computation vs LLM reasoning
│
├── README.md                               # Project documentation and test guide
└── .gitignore                              # Environment and cache exclusion rules
```

---

## Block 1: Policy Lookup by Version

### Key Requirements & Implementation
- **Tool Implementation (`tools/files.py`)**: Implements `list_files` returning direct directory entries `{name, path, type}` while enforcing strict path confinement within the workspace.
- **Skill Definition (`skills/refund-policy/SKILL.md`)**:
  - Dynamically inspects `data/policies/` using `list_files` rather than relying on hardcoded file names.
  - Resolves applicable policy strictly based on **customer purchase date**, not request date or current timestamp.
  - Requires three data points: purchase date, refund request date, and activation status. If activation status is missing, the agent halts and prompts the user for clarification.
- **Evaluation Traces**:
  - `case_a_purchase_before_oct.jsonl`: Purchased Sep 15, 2026 -> matches `policy-before-oct.md` (10-day window, eligible, 0% fee).
  - `case_b_purchase_from_oct_renamed.jsonl`: Purchased Oct 5, 2026 with renamed document -> discovers file dynamically, evaluates under updated terms.
  - `case_missing_activation_info.jsonl`: Activation status omitted -> agent prompts user without making assumptions.

---

## Block 2: Workload & Overload Verification

### Key Requirements & Implementation
- **Script Logic (`scripts/check_csv.py`)**:
  - Requires mandatory CLI argument `--max-hours` (non-negative finite float); exits non-zero on missing or invalid arguments.
  - Trims leading/trailing whitespace across `task_id`, `owner`, and `hours`.
  - **First-Occurrence Rule**: Only retains the first occurrence of each `task_id` in the file. Subsequent occurrences are flagged as `duplicate_id` and excluded from hour aggregation, even if the initial occurrence had invalid data.
  - Aggregates valid hours per owner into `hours_by_owner`.
  - Identifies `overloaded_owners` where `total_hours > max_hours` (exact boundary match is not overloaded).
  - Collects all excluded rows in `excluded_rows` sorted by line number with standardized reason codes (`wrong_field_count`, `missing_task_id`, `duplicate_id`, `missing_owner`, `invalid_hours`).
- **Skill Definition (`skills/csv-quality/SKILL.md`)**: Prompts user for threshold if omitted from the prompt. Executes `check_csv.py` via bash and parses structured JSON output.
- **Evaluation Traces**:
  - `trace_workload_threshold_8.jsonl`: Threshold 8.0h -> Lan: 9.0h (overloaded by 1.0h), Minh: 3.0h. Generates `output/workload.md`.
  - `trace_workload_threshold_9.jsonl`: Threshold 9.0h -> Lan: 9.0h, Minh: 3.0h. No owner overloaded.
  - `trace_missing_threshold.jsonl`: Threshold absent -> agent requests `--max-hours` before execution.
  - `trace_missing_file.jsonl`: Non-existent file -> script exits with code 1; agent surfaces error gracefully without generating invalid reports.

---

## Reproduction & Verification

### Run Automated Tests
```bash
# Execute CSV quality validation test suite
pytest agent-tools-skills-lab/stage-04-script-skill/tests/test_check_csv.py
```
*Result: 17 passed.*

### Run Direct CLI Checks
```bash
# Threshold = 8.0 hours
python block-2/skills/csv-quality/scripts/check_csv.py --input block-2/data/workload.csv --max-hours 8

# Threshold = 9.0 hours
python block-2/skills/csv-quality/scripts/check_csv.py --input block-2/data/workload.csv --max-hours 9

# Edge-case dataset with threshold = 0.0 hours
python block-2/skills/csv-quality/scripts/check_csv.py --input block-2/data/workload-edge.csv --max-hours 0
```
