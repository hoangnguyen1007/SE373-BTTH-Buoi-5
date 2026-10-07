from pathlib import Path
import json
import subprocess
import sys

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPT = BASE_DIR / "skills" / "csv-quality" / "scripts" / "check_csv.py"
DATA_DIR = BASE_DIR / "data"


def run(path, max_hours=8.0):
    cmd = [sys.executable, str(SCRIPT), "--input", str(path)]
    if max_hours is not None:
        cmd.extend(["--max-hours", str(max_hours)])
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)


def write_csv(tmp_path, text):
    path = tmp_path / "t.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_fixture_statistics():
    result = run(DATA_DIR / "tasks.csv")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["row_count"] == 6
    assert data["missing_owner_count"] == 1
    assert data["invalid_hours_count"] == 1
    assert data["duplicate_id_count"] == 1
    assert data["duplicate_ids"] == ["T02"]
    assert [(i["line"], i["column"], i["type"]) for i in data["issues"]] == [
        (4, "owner", "missing_owner"),
        (5, "hours", "invalid_hours"),
        (6, "task_id", "duplicate_id"),
    ]
    assert "total_hours" not in data


@pytest.mark.parametrize("hours", ["NaN", "nan", "Infinity", "-inf", "-1", ""])
def test_non_finite_negative_or_empty_hours_rejected(tmp_path, hours):
    data = json.loads(run(write_csv(tmp_path, f"task_id,owner,hours\nT01,Lan,{hours}\n")).stdout)
    assert data["invalid_hours_count"] == 1
    assert data["issues"][0]["line"] == 2


def test_clean_data_exit_0_without_issues(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\nT02,Minh,2.5\n"))
    assert result.returncode == 0
    assert json.loads(result.stdout)["issues"] == []


def test_missing_file_exit_1(tmp_path):
    result = run(tmp_path / "khong-co.csv")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Không đọc được file" in result.stderr


def test_missing_column_exit_1(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner\nT01,Lan\n"))
    assert result.returncode == 1
    assert "Thiếu cột bắt buộc: hours" in result.stderr


def test_parse_error_exit_1(tmp_path):
    result = run(write_csv(tmp_path, 'task_id,owner,hours\nT01,"La"n,4\n'))
    assert result.returncode == 1
    assert "Lỗi parse CSV" in result.stderr


def test_script_does_not_modify_input():
    source = DATA_DIR / "tasks.csv"
    before = source.read_bytes()
    run(source)
    assert source.read_bytes() == before


def test_missing_max_hours_exit_nonzero(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\n"), max_hours=None)
    assert result.returncode != 0


def test_invalid_max_hours_exit_nonzero(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\n"), max_hours=-1)
    assert result.returncode != 0
    result_nan = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\n")), "--max-hours", "invalid"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )
    assert result_nan.returncode != 0


def test_workload_threshold_8():
    result = run(DATA_DIR / "workload.csv", max_hours=8)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["hours_by_owner"] == {"Lan": 9.0, "Minh": 3.0}
    assert data["overloaded_owners"] == [{"owner": "Lan", "total_hours": 9.0}]
    assert data["excluded_rows"] == [
        {"line": 5, "task_id": "T04", "reasons": ["invalid_hours"]},
        {"line": 6, "task_id": "T02", "reasons": ["duplicate_id"]},
        {"line": 7, "task_id": "T05", "reasons": ["missing_owner"]},
    ]


def test_workload_threshold_9():
    result = run(DATA_DIR / "workload.csv", max_hours=9)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["hours_by_owner"] == {"Lan": 9.0, "Minh": 3.0}
    assert data["overloaded_owners"] == []


def test_edge_case_first_occurrence_invalid_hours():
    result = run(DATA_DIR / "workload-edge.csv", max_hours=0)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["max_hours"] == 0
    assert data["hours_by_owner"] == {"Minh": 0.0}
    assert data["overloaded_owners"] == []
    assert data["excluded_rows"] == [
        {"line": 2, "task_id": "E01", "reasons": ["invalid_hours"]},
        {"line": 3, "task_id": "E01", "reasons": ["duplicate_id"]},
    ]


