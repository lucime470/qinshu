"""SQLite 课例库。"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def _db_path() -> Path:
    """打包成 exe 后，课例库放在 exe 旁边，而不是临时解包目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "storage" / "qinshu.db"
    return ROOT / "storage" / "qinshu.db"


DB_PATH = _db_path()
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def save_lesson(chart: dict, category_code: str | None = None, judgement_text: str = "", notes: str = "",
                steps: list[dict] | None = None) -> int:
    now = _now()
    cal = chart["calendar"]
    birds = chart["birds"]
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO lessons
            (created_at, lesson_time, timezone, longitude, four_pillars_json, yuan_index,
             day_bird, hour_bird, qi_jiang, fan_qin, dao_jiang, huo_yao,
             chart_snapshot_json, category_code, judgement_text, notes, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                now,
                chart["input"]["datetime"],
                chart["input"].get("timezone", "Asia/Shanghai"),
                chart["input"].get("longitude"),
                json.dumps(cal["four_pillars"], ensure_ascii=False),
                chart["yuan"]["index"],
                birds["day"], birds["hour"], birds["qi_jiang"],
                birds["fan_qin"], birds["dao_jiang"], birds["huo_yao"],
                json.dumps(chart, ensure_ascii=False),
                category_code, judgement_text, notes, now,
            ),
        )
        lesson_id = cur.lastrowid
        for order, step in enumerate(steps or [], start=1):
            conn.execute(
                """INSERT INTO lesson_steps
                (lesson_id, step_code, step_order, facts_json, source_refs_json, user_judgement, user_notes)
                VALUES (?,?,?,?,?,?,?)""",
                (
                    lesson_id, step["step_code"], order,
                    json.dumps(step.get("facts", {}), ensure_ascii=False),
                    json.dumps(step.get("source_refs", []), ensure_ascii=False),
                    step.get("user_judgement", ""), step.get("user_notes", ""),
                ),
            )
        return int(lesson_id)


def list_lessons(q: str = "", category_code: str = "", date_from: str = "", date_to: str = "") -> list[dict]:
    sql = "SELECT * FROM lessons WHERE 1=1"
    params: list[Any] = []
    if q:
        category_codes = []
        try:
            categories = json.loads((ROOT / "data" / "rules" / "categories.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            categories = {}
        for item in categories.get("categories", []):
            if q.lower() in item.get("name", "").lower() or q.lower() in item.get("code", "").lower():
                category_codes.append(item["code"])
        clauses = ["judgement_text LIKE ?", "notes LIKE ?", "lesson_time LIKE ?"]
        params += [f"%{q}%"] * 3
        if category_codes:
            placeholders = ",".join("?" for _ in category_codes)
            clauses.append(f"category_code IN ({placeholders})")
            params += category_codes
        sql += " AND (" + " OR ".join(clauses) + ")"
    if category_code:
        sql += " AND category_code = ?"
        params.append(category_code)
    if date_from:
        sql += " AND lesson_time >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND lesson_time <= ?"
        params.append(date_to + "T23:59:59")
    sql += " ORDER BY id DESC"
    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_summary(dict(row)) for row in rows]


def _summary(row: dict) -> dict:
    row["four_pillars"] = json.loads(row.pop("four_pillars_json"))
    row.pop("chart_snapshot_json", None)
    return row


def get_lesson(lesson_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
        if row is None:
            return None
        data = dict(row)
        steps = conn.execute(
            "SELECT * FROM lesson_steps WHERE lesson_id = ? ORDER BY step_order", (lesson_id,)
        ).fetchall()
    data["four_pillars"] = json.loads(data.pop("four_pillars_json"))
    data["chart_snapshot"] = json.loads(data.pop("chart_snapshot_json"))
    data["steps"] = []
    for step in steps:
        item = dict(step)
        item["facts"] = json.loads(item.pop("facts_json") or "{}")
        item["source_refs"] = json.loads(item.pop("source_refs_json") or "[]")
        data["steps"].append(item)
    return data


def update_lesson(lesson_id: int, **fields) -> bool:
    allowed = {"judgement_text", "notes", "category_code"}
    values = {k: v for k, v in fields.items() if k in allowed}
    if not values:
        return get_lesson(lesson_id) is not None
    values["updated_at"] = _now()
    assignments = ", ".join(f"{k} = ?" for k in values)
    with _connect() as conn:
        cur = conn.execute(f"UPDATE lessons SET {assignments} WHERE id = ?", (*values.values(), lesson_id))
        return cur.rowcount > 0


def replace_steps(lesson_id: int, steps: list[dict]) -> bool:
    """整体替换某课例的逐步判断，保持 step_order 与页面顺序一致。"""
    with _connect() as conn:
        if conn.execute("SELECT 1 FROM lessons WHERE id = ?", (lesson_id,)).fetchone() is None:
            return False
        conn.execute("DELETE FROM lesson_steps WHERE lesson_id = ?", (lesson_id,))
        for order, step in enumerate(steps, start=1):
            conn.execute(
                """INSERT INTO lesson_steps
                (lesson_id, step_code, step_order, facts_json, source_refs_json, user_judgement, user_notes)
                VALUES (?,?,?,?,?,?,?)""",
                (
                    lesson_id,
                    step["step_code"],
                    step.get("step_order", order),
                    json.dumps(step.get("facts", {}), ensure_ascii=False),
                    json.dumps(step.get("source_refs", []), ensure_ascii=False),
                    step.get("user_judgement", ""),
                    step.get("user_notes", ""),
                ),
            )
        return True


def delete_lesson(lesson_id: int) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
        return cur.rowcount > 0
