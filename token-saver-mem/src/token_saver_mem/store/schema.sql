-- Token Saver Mem — unified SQLite schema
-- Merges patterns from Loom (graph) + codex-agent-mem (observations/sessions).
-- Loaded by db.py:init_db(). Uses IF NOT EXISTS for idempotency.

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ═══════════════════════════════════════════════════════════════════
-- CORE TABLES
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS nodes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    path         TEXT NOT NULL UNIQUE,
    name         TEXT NOT NULL,
    kind         TEXT NOT NULL,
    content_hash TEXT,
    summary_hash TEXT,
    summary      TEXT,
    metadata     TEXT NOT NULL DEFAULT '{}',
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind);
CREATE INDEX IF NOT EXISTS idx_nodes_updated ON nodes(updated_at DESC);

CREATE TABLE IF NOT EXISTS edges (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    from_id INTEGER NOT NULL,
    to_id   INTEGER NOT NULL,
    kind    TEXT NOT NULL,
    FOREIGN KEY(from_id) REFERENCES nodes(id),
    FOREIGN KEY(to_id)   REFERENCES nodes(id)
);
CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id);
CREATE INDEX IF NOT EXISTS idx_edges_to   ON edges(to_id);

CREATE TABLE IF NOT EXISTS observations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name TEXT NOT NULL,
    obs_type    TEXT NOT NULL,
    content     TEXT NOT NULL,
    confidence  REAL NOT NULL DEFAULT 0.5,
    session_id  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_obs_entity   ON observations(entity_name);
CREATE INDEX IF NOT EXISTS idx_obs_session  ON observations(session_id);
CREATE INDEX IF NOT EXISTS idx_obs_created  ON observations(created_at DESC);

CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    ended_at   TEXT,
    model      TEXT,
    agent      TEXT
);

CREATE TABLE IF NOT EXISTS node_visits (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id    INTEGER NOT NULL,
    session_id TEXT    NOT NULL,
    visited_at TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY(node_id)    REFERENCES nodes(id),
    FOREIGN KEY(session_id) REFERENCES sessions(id)
);
CREATE INDEX IF NOT EXISTS idx_visits_session ON node_visits(session_id, visited_at DESC);
CREATE INDEX IF NOT EXISTS idx_visits_node    ON node_visits(node_id);

CREATE TABLE IF NOT EXISTS pack_cache (
    hash       TEXT PRIMARY KEY,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ═══════════════════════════════════════════════════════════════════
-- FTS5 FULL-TEXT SEARCH ON NODES
-- ═══════════════════════════════════════════════════════════════════

CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
    name, kind, summary,
    content='nodes',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO nodes_fts(rowid, name, kind, summary)
    VALUES (new.id, new.name, new.kind, new.summary);
END;

CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, kind, summary)
    VALUES ('delete', old.id, old.name, old.kind, old.summary);
END;

CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
    INSERT INTO nodes_fts(nodes_fts, rowid, name, kind, summary)
    VALUES ('delete', old.id, old.name, old.kind, old.summary);
    INSERT INTO nodes_fts(rowid, name, kind, summary)
    VALUES (new.id, new.name, new.kind, new.summary);
END;
