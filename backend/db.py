"""
Persistencia ligera con SQLite (librería estándar, sin ORM ni dependencias
nuevas) para el histórico de incidencias triadas.

Sustituye `INCIDENCIAS_PROCESADAS` (lista en memoria de main.py), que se
perdía en cada redeploy/reinicio del contenedor en Railway. Se elige
SQLite y no Postgres a propósito: cero servidor de BD que levantar, cero
coste, coherente con el criterio "priorizar ecosistemas abiertos y
eficiencia de recursos en la fase de prototipado" del enunciado. Migrar a
Postgres más adelante solo implicaría cambiar la cadena de conexión, ya
que el resto del código consume estas funciones, no SQL directo.

Variable de entorno opcional:
    CIVICMIND_DB_PATH=/ruta/a/civicmind.db   (por defecto: ./civicmind.db)

En Railway, si se monta un volumen persistente, apuntar CIVICMIND_DB_PATH
a una ruta dentro de ese volumen; si no, la base vive en el filesystem
efímero del contenedor (sobrevive a requests pero no a un redeploy —
sigue siendo un salto enorme respecto a la lista en memoria).
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.getenv("CIVICMIND_DB_PATH", "civicmind.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS incidencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creado_en TEXT NOT NULL,
    texto TEXT NOT NULL,
    lat REAL,
    lon REAL,
    triaje_json TEXT NOT NULL,
    metricas_json TEXT NOT NULL
);
"""


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Crear la tabla si no existe. Se llama una vez al arrancar la API."""
    with _conn() as conn:
        conn.execute(_SCHEMA)


def guardar_incidencia(
    texto: str,
    triaje_dict: dict,
    metricas_dict: dict,
    lat: float | None = None,
    lon: float | None = None,
) -> int:
    """Inserta una incidencia ya triada y devuelve su id autogenerado."""
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO incidencias (creado_en, texto, lat, lon, triaje_json, metricas_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                texto,
                lat,
                lon,
                json.dumps(triaje_dict, ensure_ascii=False),
                json.dumps(metricas_dict, ensure_ascii=False),
            ),
        )
        return cur.lastrowid


def listar_incidencias(limite: int = 500) -> list[dict]:
    """
    Devuelve el histórico más reciente primero. Usado por:
    - GET /incidencias (tabla del dashboard)
    - GET /incidencias/geo (mapa — filtra las que tienen lat/lon)
    """
    with _conn() as conn:
        filas = conn.execute(
            "SELECT * FROM incidencias ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()

    resultado = []
    for f in filas:
        resultado.append(
            {
                "id": f["id"],
                "creado_en": f["creado_en"],
                "texto": f["texto"],
                "lat": f["lat"],
                "lon": f["lon"],
                "triaje": json.loads(f["triaje_json"]),
                "metricas": json.loads(f["metricas_json"]),
            }
        )
    return resultado
