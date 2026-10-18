PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS lessons (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  lesson_time TEXT NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'Asia/Shanghai',
  longitude REAL,
  four_pillars_json TEXT NOT NULL,
  yuan_index INTEGER,
  day_bird TEXT,
  hour_bird TEXT,
  qi_jiang TEXT,
  fan_qin TEXT,
  dao_jiang TEXT,
  huo_yao TEXT,
  chart_snapshot_json TEXT NOT NULL,
  category_code TEXT,
  judgement_text TEXT,
  notes TEXT,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lesson_steps (
  lesson_id INTEGER NOT NULL,
  step_code TEXT NOT NULL,
  step_order INTEGER NOT NULL,
  facts_json TEXT,
  source_refs_json TEXT,
  user_judgement TEXT,
  user_notes TEXT,
  PRIMARY KEY (lesson_id, step_code),
  FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_lessons_time ON lessons(lesson_time);
CREATE INDEX IF NOT EXISTS idx_lessons_category ON lessons(category_code);
