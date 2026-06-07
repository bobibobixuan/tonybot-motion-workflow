# Official Actions Data Schema

## Directory Structure

```
data/official-actions/
├── index.json          # Full index: all actions with metadata
├── categories.json     # Category list with counts
├── schema.md           # This file
└── actions/
    ├── 0-lizheng.json
    ├── 1-qianjin.json
    └── ...
```

## index.json

```json
{
  "total": 204,
  "categories": [
    {"key": "dance", "name": "Dance"},
    {"key": "locomotion", "name": "Locomotion"},
    ...
  ],
  "actions": [
    {
      "id": 0,
      "name": "0号立正",
      "slug": "0-lizheng",
      "category": "posture",
      "frame_count": 1,
      "total_duration": 500
    },
    ...
  ]
}
```

## Action JSON (`actions/<id>-<slug>.json`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Action ID (from filename prefix) |
| `name` | string | Original filename stem |
| `slug` | string | URL-safe identifier |
| `source_file` | string | Original .rob filename |
| `category` | string | Category key |
| `category_name` | string | Human-readable category name |
| `tags` | string[] | Tags (includes category) |
| `frame_count` | int | Number of frames |
| `total_duration` | int | Total duration in ms |
| `source_tag` | string | ACT-40 tag ("EYPT" or "plain") |
| `source_sha256` | string | SHA-256 of original .rob file |
| `frames` | array | Frame data |

### Frame Object

| Field | Type | Description |
|-------|------|-------------|
| `index` | int | 0-based frame index |
| `duration` | int | Frame duration in ms |
| `pose` | int[16] | 16 servo values (ID1–ID16), range 0–1000 |

## Category Legend

| Key | Name | Description |
|-----|------|-------------|
| `posture` | Posture | Stand, bow, neutral poses |
| `locomotion` | Locomotion | Forward, backward, turn, track |
| `punch` | Punch | Punches, hooks, boxing |
| `kick` | Kick | Kicks, shoot |
| `squat` | Squat | Squat, crouch |
| `twist` | Twist | Waist twist |
| `slide` | Slide | Side slide |
| `greeting` | Greeting | Wave, greet gestures |
| `dance` | Dance | Dance choreography |
| `choreography` | Choreography | Multi-action choreography |
| `floor` | Floor | Pushup, situp |
| `manipulation` | Manipulation | Grab, carry, drop |
| `other` | Other | Unclassified |
