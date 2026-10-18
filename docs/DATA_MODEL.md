# 演禽起课器 数据模型与接口

## 1. 分层

```
前端页面
  → API（JSON）
    → 盘面服务（core）
      → 历法层、规则层、关系层
    → 课例服务
      → SQLite
```

前端不得自行推算禽星，也不得自行拼接断语；所有盘面与证据由后端返回。

## 2. 核心对象

### 2.1 `ChartInput`

```json
{
  "datetime": "2026-10-18T14:30:00",
  "timezone": "Asia/Shanghai",
  "use_current_time": false,
  "longitude": null
}
```

- `datetime` 按北京时间解析。
- `longitude` 为空时不生成真太阳时对照盘。
- 指定时间与当前时间共用同一套算法。
- `solar_time_variant` 为 null 时，前端不显示对照盘；非空时返回 `longitude`、`local_time`、`four_pillars`、`longitude_minutes`、`equation_minutes`、`note`。真太阳时按经度差加均时差换算，只作对照。

### 2.2 `ChartResult`

```json
{
  "input": {},
  "calendar": {
    "four_pillars": {"year": "壬寅", "month": "乙巳", "day": "丁丑", "hour": "乙巳"},
    "solar_term": "小满",
    "month_branch": "巳",
    "day_boundary": "23:00",
    "solar_time_variant": null
  },
  "yuan": {"index": 7, "name": "七元", "leader_bird": "箕水豹", "day_index": 14},
  "birds": {
    "day": "觜火猴",
    "hour": "危月燕",
    "qi_jiang": "箕水豹",
    "fan_qin": "胃土雉",
    "dao_jiang": "井木犴",
    "huo_yao": "参水猿"
  },
  "comparison": {
    "fan_qin_alt": "心月狐",
    "dao_jiang_alt": "张月鹿",
    "source": "禽星易见系辅助起法"
  },
  "relations": {
    "self": "翻禽",
    "other": "倒将",
    "same_bird": false,
    "sheng_ke": {},
    "he": [],
    "chong": [],
    "sanhe": [],
    "fei_fu": {"觜火猴": "飞", "危月燕": "飞", "胃土雉": "飞", "井木犴": "飞", "箕水豹": "伏", "参水猿": "飞"},
    "suo_bo": {},
    "suo_bo_facts": {
      "inner": {"name": "田", "day_branch": "丑", "source": "演禽正传 PDF第28页（印刷第20页）"},
      "outer": {
        "hour": {
          "bird": "危月燕", "luminary": "月", "start_branch": "未", "hour_branch": "巳",
          "branch": "巳", "column": "汤火", "path": [],
          "judgement": {"column": "汤火", "label": "不妨", "text": "天禽不妨", "matched_by": "category"}
          ,
          "de_di": {"status": "得地", "matched": true, "label": "不妨", "column": "汤火", "text": "天禽不妨"}
        }
      },
      "de_di": {"hour": {"status": "得地", "matched": true, "label": "不妨"}},
      "xing_hai": {"hour": []},
      "fuduan": {"day_branch": "丑", "target": "斗", "hour_bird": "危月燕", "matched": false,
                  "source_book": "禽星易见", "source_page": "伏断", "original_text": "……"}
    },
    "xing_hai": {"self": [], "other": [], "day": [], "hour": []},
    "outer_hour": {},
    "strength": {"危月燕": {"season": "夏", "status": "衰", "month_branch": "巳", "matched": false}},
    "season": "巳"
  },
  "evidence": [],
  "warnings": []
}
```

### 2.3 `CategoryReading`

```json
{
  "category_code": "marriage",
  "category_name": "婚姻",
  "role_map": {
    "primary_book": "演禽正传",
    "roles": [
      {"role": "男", "bird": "番禽"},
      {"role": "女", "bird": "时禽"},
      {"role": "媒人", "bird": "日禽"}
    ]
  },
  "matched_rules": [],
  "all_rules": [],
  "conflicts": []
}
```

### 2.4 `RuleEvidence`

```json
{
  "rule_id": "yz-marriage-001",
  "source_book": "演禽正传",
  "source_chapter": "婚姻匹配章",
  "source_page": "57",
  "original_text": "……",
  "condition": {},
  "priority": "primary",
  "conflict_group": "marriage-role-map"
}
```

### 2.4.1 `BirdProfile` 的 `suo_bo_dial`

`GET /api/birds` 与 `GET /api/birds/{code}` 的每只禽星都返回锁泊圆盘所需的三层对应，页面不再自行推算：

```json
{
  "suo_bo_dial": {
    "inner": {"子": "湖", "丑": "田", "…": "…"},
    "outer_columns": {"山": "申", "水": "酉", "…": "…"},
    "outer_start": "申",
    "outer_luminary": "水"
  }
}
```

- `inner`：十二地支 → 内锁泊宫，取自 `qiyuan.json::suo_bo.inner`。
- `outer_columns`：外锁泊宫 → 该宫所对应的地支；按本禽七曜长生位起山，顺排十二宫。
- `outer_start`：本禽外锁泊起山的地支；`outer_luminary` 为所依据的七曜。

圆盘只呈现这组“地支 → 内锁泊 → 外锁泊”对应；外锁泊吉凶、得地、刑害等仍走 `suo_bo_facts`，不在圆盘内混排。

## 2.5 冻结约定（第 0 轮）

### 禽星编码

`bird_code` 固定为 `B01`–`B28`，编号即二十八宿标准序，不采用拼音码，避免“壁/毕”“氐/帝”等同音冲突。

| code | 标准名 | code | 标准名 | code | 标准名 | code | 标准名 |
|---|---|---|---|---|---|---|---|
| `B01` | 角木蛟 | `B08` | 斗木獬 | `B15` | 奎木狼 | `B22` | 井木犴 |
| `B02` | 亢金龙 | `B09` | 牛金牛 | `B16` | 娄金狗 | `B23` | 鬼金羊 |
| `B03` | 氐土貉 | `B10` | 女土蝠 | `B17` | 胃土雉 | `B24` | 柳土獐 |
| `B04` | 房日兔 | `B11` | 虚日鼠 | `B18` | 昴日鸡 | `B25` | 星日马 |
| `B05` | 心月狐 | `B12` | 危月燕 | `B19` | 毕月乌 | `B26` | 张月鹿 |
| `B06` | 尾火虎 | `B13` | 室火猪 | `B20` | 觜火猴 | `B27` | 翼火蛇 |
| `B07` | 箕水豹 | `B14` | 壁水貐 | `B21` | 参水猿 | `B28` | 轸水蚓 |

规则：

- 编码只表示标准序，不表示七元中的位置。
- 对外唯一主键是 `bird_code`；显示名、异体名放在 `name`、`aliases`。
- API 中 `birds` 字段允许返回完整宿名，也允许返回 `bird_code`；第一版固定返回完整宿名，另在资源接口用 `bird_code` 查询。
- 前端不得从宿名推断编码，必须使用后端给的映射。

### 冻结字段

`ChartResult` 顶层固定为：`input`、`calendar`、`yuan`、`birds`、`relations`、`comparison`、`evidence`、`warnings`。

- `calendar.four_pillars` 固定为 `year`、`month`、`day`、`hour` 四键，值为完整干支。
- `calendar` 额外固定返回 `solar_term`、`month_branch`、`day_boundary`、`solar_time_variant`。
- `yuan` 固定返回 `index`、`name`、`leader_bird`、`day_index`，`index` 从 1 开始，范围 1–7。
- `birds` 固定返回 `day`、`hour`、`qi_jiang`、`fan_qin`、`dao_jiang`、`huo_yao` 六个完整宿名。
- `comparison` 为辅助体系差异，第一版固定包含 `fan_qin_alt`、`dao_jiang_alt`、`source`；无差异时三个键仍返回 `null`/`null`/`null`。
- `relations` 固定返回 `self`、`other`、`same_bird`、`self_label`、`other_label`、`sheng_ke`、`he`、`chong`、`sanhe`、`sanhe_with_day`、`day_time_sanhe`、`fei_fu`、`suo_bo`、`suo_bo_facts`、`xing_hai`、`outer_hour`、`fuduan`、`strength`、`season`。其中 `suo_bo_facts.outer` 覆盖 `day`、`hour`、`qi_jiang`、`fan_qin`、`dao_jiang`、`huo_yao` 六类盘面禽星；`suo_bo_facts.de_di` 按同一组键返回得地/不得地事实；`fei_fu` 以禽名为键，覆盖同样六类，同名禽星只保留一键。
- `warnings` 每项固定为 `{code, message, source}`；`evidence` 每项固定为 `{rule_id, source_book, source_chapter, source_page, original_text}`。

### 冻结 API

| 方法 | 路径 | 请求 | 成功响应 | 失败响应 |
|---|---|---|---|---|
| `POST` | `/api/chart` | `ChartInput` | `ChartResult` | `{"error":{"code","message"}}` |
| `POST` | `/api/guide` | `{"chart": ChartResult}` | `{"steps":[GuideStep]}` | 同上 |
| `GET` | `/api/birds/{code}` | 无 | `BirdProfile` | 同上 |
| `GET` | `/api/categories` | 无 | `{"categories":[...]}` | 同上 |
| `POST` | `/api/reading` | `{"chart": ChartResult, "category_code": string}` | `CategoryReading` | 同上 |
| `GET` | `/api/lessons` | 查询参数 `q`、`category_code`、`from`、`to` | `{"lessons":[...]}` | 同上 |
| `POST` | `/api/lessons` | `LessonCreate` | `{"id": integer}` | 同上 |
| `GET` | `/api/lessons/{id}` | 无 | `LessonDetail` | 404 |
| `PATCH` | `/api/lessons/{id}` | 可更新 `judgement_text`、`notes`、`category_code`、`steps` | `{"ok":true}` | 404 |
| `DELETE` | `/api/lessons/{id}` | 无 | `{"ok":true}` | 404 |

约定：`/api/chart` 不写库；`/api/lessons` 只写课例；所有响应 `Content-Type: application/json; charset=utf-8`；错误码第一版固定为 `invalid_input`、`not_found`、`internal_error`。

### `GET /api/lessons` 检索语义

- `q`：关键词，匹配 `judgement_text`、`notes`、`lesson_time`，以及占类名称或占类编码；匹配占类时返回该占类下的全部课例。
- `category_code`：按占类编码精确筛选。
- `from` / `to`：按课例时间筛选，格式为 `YYYY-MM-DD`；`from` 从当日 `00:00:00` 起算，`to` 包含结束日，截止到 `T23:59:59`。
- 多组参数同时出现时以 AND 组合；结果按课例 `id` 倒序返回。

### `GuideStep`

```json
{
  "step_code": "suo_bo",
  "order": 8,
  "title": "锁泊与宫位",
  "question": "内外锁泊落在何宫？是否得地、刑害或逢伏断？",
  "facts": {},
  "source_refs": [{"book": "演禽正传", "chapter": "外锁泊", "page": "PDF第29页（印刷第21页）"}]
}
```

十步固定为：`time`、`yuan_day`、`hour_qijiang`、`fan_dao_huoyao`、`sheng_ke`、`fei_fu`、`he_chong`、`suo_bo`、`category`、`judgement`。步骤事实全部由后端从 `ChartResult` 生成，前端不自行推算。

## 3. 数据库表

### `lessons`

```sql
CREATE TABLE lessons (
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
```

### `lesson_steps`

```sql
CREATE TABLE lesson_steps (
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
```

### `category_rules`

```sql
CREATE TABLE category_rules (
  id TEXT PRIMARY KEY,
  category_code TEXT NOT NULL,
  category_name TEXT NOT NULL,
  book TEXT NOT NULL,
  role_map_json TEXT,
  condition_json TEXT,
  original_text TEXT NOT NULL,
  source_page TEXT,
  conflict_group TEXT,
  priority TEXT NOT NULL
);
```

### `bird_profiles`

```sql
CREATE TABLE bird_profiles (
  bird_code TEXT PRIMARY KEY,
  standard_name TEXT NOT NULL,
  aliases TEXT,
  seven_luminary TEXT NOT NULL,
  element TEXT,
  day_night TEXT,
  nature_text TEXT,
  source_refs_json TEXT
);
```

### `settings`

```sql
CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

## 4. API 草案

| 方法 | 路径 | 作用 |
|---|---|---|
| `POST` | `/api/chart` | 由时间生成盘面 |
| `POST` | `/api/guide` | 由盘面生成固定十步事实与出处 |
| `GET` | `/api/categories` | 占类列表 |
| `POST` | `/api/reading` | 生成占类对照 |
| `GET` | `/api/lessons` | 课例列表与检索 |
| `POST` | `/api/lessons` | 保存课例 |
| `GET` | `/api/lessons/{id}` | 读取课例 |
| `PATCH` | `/api/lessons/{id}` | 更新判断、备注与逐步判断 |
| `DELETE` | `/api/lessons/{id}` | 删除课例 |
| `GET` | `/api/birds/{code}` | 禽星详情与出处 |

约定：

- 所有错误返回 `{ "error": { "code": "...", "message": "..." } }`。
- 盘面接口必须返回 `warnings`，用于标注规则待核或版本差异。
- 删除接口只删除课例，不删除规则和书籍资料。

## 5. 课例保存粒度

第一版保存：

- 输入时间、时区、经度。
- 四柱、节气、七元。
- 完整盘面快照。
- 所选占类。
- 固定引导每一步的判断和备注。
- 最终判断与备注。

第一版不保存：

- 自由问答对话。
- 页面滚动位置、临时展开状态等界面状态。

结构上预留 `all_rules`、`conflicts` 和未来对话记录的扩展位置，但第一版不启用。
