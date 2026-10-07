#!/usr/bin/env python3
"""Kiểm tra chất lượng CSV công việc (task_id, owner, hours) và tính tổng giờ theo người.

Cách chạy (cwd là workspace):
    python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8

Exit 0: phân tích thành công, kể cả khi dữ liệu có lỗi chất lượng hoặc người quá tải.
Exit 1: file không tồn tại/không đọc được, thiếu cột bắt buộc hoặc lỗi parse CSV.
Exit 2: thiếu hoặc sai tham số dòng lệnh (--max-hours).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys

# Ensure UTF-8 output on all systems including Windows default console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REQUIRED_COLUMNS = ("task_id", "owner", "hours")

REASON_ORDER = ("wrong_field_count", "missing_task_id", "duplicate_id", "missing_owner", "invalid_hours")


class InputError(Exception):
    pass


def parse_hours(raw: str | None) -> float | None:
    """Số giờ hợp lệ: số hữu hạn, không âm. Trả None nếu không hợp lệ."""
    if raw is None or not raw.strip():
        return None
    try:
        value = float(raw.strip())
    except ValueError:
        return None
    if not math.isfinite(value) or value < 0:
        return None
    return value


def validate_max_hours(raw: str) -> float:
    try:
        value = float(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{raw}' không phải là số hợp lệ.")
    if not math.isfinite(value) or value < 0:
        raise argparse.ArgumentTypeError(f"'{raw}' phải là số hữu hạn không âm.")
    return value


def analyze(path: str, max_hours: float) -> dict:
    try:
        handle = open(path, encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise InputError(f"Không đọc được file {path}: {exc.strerror or exc}") from exc
    with handle:
        reader = csv.reader(handle, strict=True)
        try:
            header = next(reader, None)
            if header is None:
                raise InputError(f"File {path} rỗng, không có header.")
            columns = [c.strip() for c in header]
            missing = [c for c in REQUIRED_COLUMNS if c not in columns]
            if missing:
                raise InputError(f"Thiếu cột bắt buộc: {', '.join(missing)}. Header hiện có: {', '.join(columns)}")
            index = {name: columns.index(name) for name in REQUIRED_COLUMNS}

            row_count = 0
            missing_owner = 0
            invalid_hours = 0
            first_seen: dict[str, int] = {}
            duplicate_ids: list[str] = []
            issues: list[dict] = []

            hours_by_owner: dict[str, float] = {}
            excluded_rows: list[dict] = []

            for row in reader:
                line = reader.line_num
                if not any(cell.strip() for cell in row):
                    continue  # bỏ qua dòng trống
                row_count += 1

                def cell(name: str) -> str:
                    position = index[name]
                    return row[position].strip() if position < len(row) else ""

                task_id, owner, hours = cell("task_id"), cell("owner"), cell("hours")

                is_wrong_field_count = (len(row) != len(columns))
                if is_wrong_field_count:
                    issues.append({"line": line, "column": None, "type": "wrong_field_count", "task_id": task_id or None,
                                   "message": f"Có {len(row)} trường, header có {len(columns)} cột."})

                is_missing_task_id = not task_id
                is_duplicate_id = False
                if is_missing_task_id:
                    issues.append({"line": line, "column": "task_id", "type": "missing_task_id", "task_id": None,
                                   "message": "task_id trống."})
                elif task_id in first_seen:
                    is_duplicate_id = True
                    if task_id not in duplicate_ids:
                        duplicate_ids.append(task_id)
                    issues.append({"line": line, "column": "task_id", "type": "duplicate_id", "task_id": task_id,
                                   "message": f"task_id {task_id} đã xuất hiện ở line {first_seen[task_id]}."})
                else:
                    first_seen[task_id] = line

                is_missing_owner = not owner
                if is_missing_owner:
                    missing_owner += 1
                    issues.append({"line": line, "column": "owner", "type": "missing_owner", "task_id": task_id or None,
                                   "message": "owner trống."})

                parsed_h = parse_hours(hours)
                is_invalid_hours = (parsed_h is None)
                if is_invalid_hours:
                    invalid_hours += 1
                    issues.append({"line": line, "column": "hours", "type": "invalid_hours", "task_id": task_id or None,
                                   "value": hours, "message": f"hours '{hours}' không phải số hữu hạn không âm."})

                # Determine exclusion reasons in fixed order
                reasons = []
                if is_wrong_field_count:
                    reasons.append("wrong_field_count")
                if is_missing_task_id:
                    reasons.append("missing_task_id")
                if is_duplicate_id:
                    reasons.append("duplicate_id")
                if is_missing_owner:
                    reasons.append("missing_owner")
                if is_invalid_hours:
                    reasons.append("invalid_hours")

                if reasons:
                    excluded_rows.append({
                        "line": line,
                        "task_id": task_id if task_id else None,
                        "reasons": reasons,
                    })
                else:
                    hours_by_owner[owner] = hours_by_owner.get(owner, 0.0) + parsed_h
        except csv.Error as exc:
            raise InputError(f"Lỗi parse CSV ở line {reader.line_num}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise InputError(f"File {path} không phải UTF-8: {exc}") from exc

    overloaded_owners = [
        {"owner": o, "total_hours": hours_by_owner[o]}
        for o in sorted(hours_by_owner.keys())
        if hours_by_owner[o] > max_hours
    ]

    return {
        "input": path,
        "row_count": row_count,
        "missing_owner_count": missing_owner,
        "invalid_hours_count": invalid_hours,
        "duplicate_id_count": len(duplicate_ids),
        "duplicate_ids": duplicate_ids,
        "issues": sorted(issues, key=lambda item: item["line"]),
        "max_hours": max_hours,
        "hours_by_owner": hours_by_owner,
        "overloaded_owners": overloaded_owners,
        "excluded_rows": sorted(excluded_rows, key=lambda item: item["line"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kiểm tra chất lượng CSV công việc và tính tổng giờ.")
    parser.add_argument("--input", required=True, help="Đường dẫn CSV, ví dụ data/workload.csv")
    parser.add_argument("--max-hours", required=True, type=validate_max_hours, help="Ngưỡng giờ tối đa (số hữu hạn không âm)")
    args = parser.parse_args(argv)
    try:
        result = analyze(args.input, args.max_hours)
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
