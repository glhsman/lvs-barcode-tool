"""
Alle Datenbankoperationen für Barcode Forge.

Konventionen:
  - Jede Funktion holt eine eigene Verbindung aus dem Pool und gibt sie zurück.
  - Rückgabe von Dataclass-Instanzen aus models.types.
"""
from __future__ import annotations

import json
from typing import Optional

import mysql.connector

from db.connection import get_connection
from models.types import (
    Project, ProjectField, DataRecord, LabelFormat, LabelObject, SavedLabel,
)


# ──────────────────────────────────────────────────────────────────────────────
# Projekte
# ──────────────────────────────────────────────────────────────────────────────

def list_projects() -> list[Project]:
    conn = get_connection()
    if conn is None: return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, name, description FROM projects ORDER BY name")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [Project(id=r["id"], name=r["name"], description=r.get("description","")) for r in rows]
    except Exception:
        return []


def create_project(name: str, description: str = "") -> Project:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO projects (name, description) VALUES (%s, %s)",
        (name, description),
    )
    conn.commit()
    pid = cur.lastrowid
    cur.close(); conn.close()
    # Standardformat anlegen
    _ensure_label_format(pid)
    return Project(id=pid, name=name, description=description)


def rename_project(project_id: int, new_name: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE projects SET name=%s WHERE id=%s", (new_name, project_id))
    conn.commit()
    cur.close(); conn.close()


def delete_project(project_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM projects WHERE id=%s", (project_id,))
    conn.commit()
    cur.close(); conn.close()


def touch_project(project_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE projects SET modified_at=NOW() WHERE id=%s", (project_id,))
    conn.commit()
    cur.close(); conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# Felder
# ──────────────────────────────────────────────────────────────────────────────

def list_fields(project_id: int) -> list[ProjectField]:
    conn = get_connection()
    if conn is None: return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, project_id, name, position FROM project_fields "
            "WHERE project_id=%s ORDER BY position, id",
            (project_id,),
        )
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [ProjectField(**r) for r in rows]
    except Exception:
        return []


def add_field(project_id: int, name: str) -> ProjectField:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(MAX(position),0)+1 FROM project_fields WHERE project_id=%s",
        (project_id,),
    )
    pos = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO project_fields (project_id, name, position) VALUES (%s,%s,%s)",
        (project_id, name, pos),
    )
    conn.commit()
    fid = cur.lastrowid
    cur.close(); conn.close()
    touch_project(project_id)
    return ProjectField(id=fid, project_id=project_id, name=name, position=pos)


def rename_field(field_id: int, new_name: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE project_fields SET name=%s WHERE id=%s", (new_name, field_id))
    conn.commit()
    cur.close(); conn.close()


def delete_field(field_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM project_fields WHERE id=%s", (field_id,))
    conn.commit()
    cur.close(); conn.close()


def reorder_fields(project_id: int, field_ids: list[int]) -> None:
    conn = get_connection()
    cur = conn.cursor()
    for pos, fid in enumerate(field_ids):
        cur.execute(
            "UPDATE project_fields SET position=%s WHERE id=%s AND project_id=%s",
            (pos, fid, project_id),
        )
    conn.commit()
    cur.close(); conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# Datensätze
# ──────────────────────────────────────────────────────────────────────────────

def list_records(project_id: int) -> list[DataRecord]:
    conn = get_connection()
    if conn is None: return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, project_id, selected, position FROM data_records "
            "WHERE project_id=%s ORDER BY position, id",
            (project_id,),
        )
        rows = cur.fetchall()
        records = {r["id"]: DataRecord(
            id=r["id"], project_id=r["project_id"],
            selected=bool(r["selected"]), position=r["position"],
        ) for r in rows}

        if records:
            placeholders = ",".join(["%s"] * len(records))
            cur.execute(
                f"SELECT rv.record_id, pf.name, rv.value "
                f"FROM record_values rv "
                f"JOIN project_fields pf ON pf.id = rv.field_id "
                f"WHERE rv.record_id IN ({placeholders})",
                list(records.keys()),
            )
            for row in cur.fetchall():
                records[row["record_id"]].values[row["name"]] = row["value"] or ""

        cur.close(); conn.close()
        return list(records.values())
    except Exception:
        return []


def add_record(project_id: int, values: dict[str, str], selected: bool = True) -> DataRecord:
    conn = get_connection()
    if conn is None: return DataRecord(id=0, project_id=0, selected=False, position=0, values={})
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT COALESCE(MAX(position),0)+1 FROM data_records WHERE project_id=%s",
        (project_id,),
    )
    pos = cur.fetchone()["COALESCE(MAX(position),0)+1"]

    cur.execute(
        "INSERT INTO data_records (project_id, selected, position) VALUES (%s,%s,%s)",
        (project_id, int(selected), pos),
    )
    rid = cur.lastrowid

    _write_record_values(cur, rid, project_id, values)
    conn.commit()
    cur.close(); conn.close()
    touch_project(project_id)
    return DataRecord(id=rid, project_id=project_id, selected=selected,
                      position=pos, values=values)


def update_record(record: DataRecord) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE data_records SET selected=%s WHERE id=%s",
        (int(record.selected), record.id),
    )
    cur.execute(
        "DELETE FROM record_values WHERE record_id=%s", (record.id,)
    )
    _write_record_values(cur, record.id, record.project_id, record.values)
    conn.commit()
    cur.close(); conn.close()
    touch_project(record.project_id)


def delete_records(record_ids: list[int]) -> None:
    if not record_ids:
        return
    conn = get_connection()
    cur = conn.cursor()
    placeholders = ",".join(["%s"] * len(record_ids))
    cur.execute(f"DELETE FROM data_records WHERE id IN ({placeholders})", record_ids)
    conn.commit()
    cur.close(); conn.close()


def set_record_selected(record_ids: list[int], selected: bool) -> None:
    if not record_ids:
        return
    conn = get_connection()
    cur = conn.cursor()
    placeholders = ",".join(["%s"] * len(record_ids))
    val = int(selected)
    cur.execute(
        f"UPDATE data_records SET selected={val} WHERE id IN ({placeholders})",
        record_ids,
    )
    conn.commit()
    cur.close(); conn.close()


def _write_record_values(cur, record_id: int, project_id: int, values: dict[str, str]) -> None:
    cur.execute(
        "SELECT id, name FROM project_fields WHERE project_id=%s", (project_id,)
    )
    rows = cur.fetchall()
    if rows and isinstance(rows[0], dict):
        field_map = {row["name"]: row["id"] for row in rows}
    else:
        field_map = {row[1]: row[0] for row in rows}
    for fname, fval in values.items():
        fid = field_map.get(fname)
        if fid is not None:
            cur.execute(
                "INSERT INTO record_values (record_id, field_id, value) VALUES (%s,%s,%s)",
                (record_id, fid, fval),
            )


# ──────────────────────────────────────────────────────────────────────────────
# Etikettenformat
# ──────────────────────────────────────────────────────────────────────────────

def _ensure_label_format(project_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT IGNORE INTO label_formats (project_id) VALUES (%s)", (project_id,)
    )
    conn.commit()
    cur.close(); conn.close()


def get_label_format(project_id: int) -> LabelFormat:
    _ensure_label_format(project_id)
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM label_formats WHERE project_id=%s", (project_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return LabelFormat(
        id=row["id"], project_id=row["project_id"],
        manufacturer=row.get("manufacturer",""), product_name=row.get("product_name",""),
        width_mm=row["width_mm"], height_mm=row["height_mm"],
        margin_top_mm=row["margin_top_mm"], margin_bottom_mm=row["margin_bottom_mm"],
        margin_left_mm=row["margin_left_mm"], margin_right_mm=row["margin_right_mm"],
        cols=row["cols"], rows=row["rows"],
        col_gap_mm=row["col_gap_mm"], row_gap_mm=row["row_gap_mm"],
    )


def save_label_format(fmt: LabelFormat) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO label_formats
            (project_id,manufacturer,product_name,
             width_mm,height_mm,
             margin_top_mm,margin_bottom_mm,margin_left_mm,margin_right_mm,
             `cols`,`rows`,col_gap_mm,row_gap_mm)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON DUPLICATE KEY UPDATE
             manufacturer=VALUES(manufacturer), product_name=VALUES(product_name),
             width_mm=VALUES(width_mm), height_mm=VALUES(height_mm),
             margin_top_mm=VALUES(margin_top_mm), margin_bottom_mm=VALUES(margin_bottom_mm),
             margin_left_mm=VALUES(margin_left_mm), margin_right_mm=VALUES(margin_right_mm),
             `cols`=VALUES(`cols`), `rows`=VALUES(`rows`),
             col_gap_mm=VALUES(col_gap_mm), row_gap_mm=VALUES(row_gap_mm)""",
        (fmt.project_id, fmt.manufacturer, fmt.product_name,
         fmt.width_mm, fmt.height_mm,
         fmt.margin_top_mm, fmt.margin_bottom_mm,
         fmt.margin_left_mm, fmt.margin_right_mm,
         fmt.cols, fmt.rows, fmt.col_gap_mm, fmt.row_gap_mm),
    )
    conn.commit()
    cur.close(); conn.close()
    touch_project(fmt.project_id)


# ──────────────────────────────────────────────────────────────────────────────
# Etikettenobjekte
# ──────────────────────────────────────────────────────────────────────────────

def list_label_objects(project_id: int) -> list[LabelObject]:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM label_objects WHERE project_id=%s ORDER BY z_order, id",
        (project_id,),
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    result = []
    for r in rows:
        props = r["properties"]
        if isinstance(props, str):
            props = json.loads(props)
        elif props is None:
            props = {}
        result.append(LabelObject(
            id=r["id"], project_id=r["project_id"], type=r["type"],
            x_mm=r["x_mm"], y_mm=r["y_mm"],
            width_mm=r["width_mm"], height_mm=r["height_mm"],
            rotation=r["rotation"], z_order=r["z_order"],
            properties=props,
        ))
    return result


def add_label_object(obj: LabelObject) -> LabelObject:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO label_objects
           (project_id,type,x_mm,y_mm,width_mm,height_mm,rotation,z_order,properties)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (obj.project_id, obj.type, obj.x_mm, obj.y_mm,
         obj.width_mm, obj.height_mm, obj.rotation, obj.z_order,
         json.dumps(obj.properties)),
    )
    conn.commit()
    obj.id = cur.lastrowid
    cur.close(); conn.close()
    touch_project(obj.project_id)
    return obj


def update_label_object(obj: LabelObject) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """UPDATE label_objects SET
           type=%s, x_mm=%s, y_mm=%s, width_mm=%s, height_mm=%s,
           rotation=%s, z_order=%s, properties=%s
           WHERE id=%s""",
        (obj.type, obj.x_mm, obj.y_mm, obj.width_mm, obj.height_mm,
         obj.rotation, obj.z_order, json.dumps(obj.properties), obj.id),
    )
    conn.commit()
    cur.close(); conn.close()
    touch_project(obj.project_id)


def delete_label_object(obj_id: int, project_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM label_objects WHERE id=%s", (obj_id,))
    conn.commit()
    cur.close(); conn.close()
    touch_project(project_id)


# ──────────────────────────────────────────────────────────────────────────────
# Gespeicherte Etiketten
# ──────────────────────────────────────────────────────────────────────────────

def save_label(label: SavedLabel) -> SavedLabel:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO saved_labels
           (project_id, record_id, name, image_data, image_format, dpi, created_by)
           VALUES (%s,%s,%s,%s,%s,%s,%s)""",
        (label.project_id, label.record_id, label.name,
         label.image_data, label.image_format, label.dpi, label.created_by),
    )
    conn.commit()
    label.id = cur.lastrowid
    cur.close(); conn.close()
    return label


def list_saved_labels(project_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id, record_id, name, image_format, dpi, created_at, created_by "
        "FROM saved_labels WHERE project_id=%s ORDER BY created_at DESC",
        (project_id,),
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


def load_saved_label(label_id: int) -> Optional[bytes]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT image_data FROM saved_labels WHERE id=%s", (label_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return bytes(row[0]) if row else None


def delete_saved_label(label_id: int) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM saved_labels WHERE id=%s", (label_id,))
    conn.commit()
    cur.close(); conn.close()
# ──────────────────────────────────────────────────────────────────────────────
# Globale Etiketten-Vorlagen (Templates)
# ──────────────────────────────────────────────────────────────────────────────

def list_global_templates() -> list[tuple[str, dict]]:
    conn = get_connection()
    if conn is None: return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM global_label_templates ORDER BY name")
        rows = cur.fetchall()
        cur.close(); conn.close()
        # Rückgabeformat kompatibel zum alten JSON-Lader machen
        return [(r["name"], {k: v for k, v in r.items() if k not in ("id", "name")}) for r in rows]
    except Exception:
        return []

def add_global_template(name: str, fmt: LabelFormat) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO global_label_templates 
           (name, manufacturer, product_name, width_mm, height_mm, 
            margin_top_mm, margin_bottom_mm, margin_left_mm, margin_right_mm, 
            `cols`, `rows`, col_gap_mm, row_gap_mm)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE 
             manufacturer=VALUES(manufacturer), product_name=VALUES(product_name),
             width_mm=VALUES(width_mm), height_mm=VALUES(height_mm),
             margin_top_mm=VALUES(margin_top_mm), margin_bottom_mm=VALUES(margin_bottom_mm),
             margin_left_mm=VALUES(margin_left_mm), margin_right_mm=VALUES(margin_right_mm),
             `cols`=VALUES(`cols`), `rows`=VALUES(`rows`),
             col_gap_mm=VALUES(col_gap_mm), row_gap_mm=VALUES(row_gap_mm)""",
        (name, fmt.manufacturer, fmt.product_name, fmt.width_mm, fmt.height_mm,
         fmt.margin_top_mm, fmt.margin_bottom_mm, fmt.margin_left_mm, fmt.margin_right_mm,
         fmt.cols, fmt.rows, fmt.col_gap_mm, fmt.row_gap_mm),
    )
    conn.commit()
    cur.close(); conn.close()

def delete_global_template(name: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM global_label_templates WHERE name=%s", (name,))
    conn.commit()
    cur.close(); conn.close()
