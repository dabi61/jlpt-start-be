# Database Schema

## 1. User Management (`apps.users.models.User`)
Custom user model extending `AbstractUser`.
- `id` (PK): Internal primary key.
- `email` (Unique): Login identifier.
- `display_name`: User's visible name.
- `avatar`: URL to profile picture.
- `role`: `USER` | `ADMIN`.
- `login_method`: `EMAIL` | `GOOGLE` | `FACEBOOK`.
- `level`: Current target JLPT level (`N6`-`N1`).
- `streak`: Current daily learning streak.
- `last_study_date`: Last active date.

## 2. Learning Structure (`apps.learning`)

### Lesson (`Lesson`)
Highest level grouping of content.
- `lession_name`: Title.
- `level`: JLPT Level (N5-N1).

### Unit (`Unit`)
Sub-division of lessons.
- `unit_name`: Title.
- `unit_type`: Type of content in this unit (`vocabulary`, `grammar`, `kanji`, `mixed`).
- `lession_id`: Foreign Key reference to Lesson (currently Text/ID).
- `level`: JLPT Level.

### Progress (`UserUnitProgress`)
Tracks completion status.
- `user_id`: Link to User.
- `unit_id`: Link to Unit.
- `lession_id`: Link to Lesson.
- `progress`: Completion status/percentage.
- `completed_at`: Timestamp.

### Unit Anki Cards (`UnitAnkiCard`)
Per-user scheduling state for each item inside one unit.
- `unit_id`, `user_id`: User-unit ownership.
- `item_type`: `vocabulary` | `grammar` | `kanji`.
- `item_id`: Linked content item ID.
- `state`: `new` | `learning` | `relearning` | `review`.
- `step_index`: Current learning step index.
- `interval_days`: Next interval in days for review cards.
- `ease_factor`: SM-2 ease factor.
- `reps`, `lapses`: Review counters.
- `due_at`, `last_reviewed_at`: Scheduling timestamps.

### Unit Anki Review Logs (`UnitAnkiReviewLog`)
Immutable history of each answer button click.
- `card`: FK to `UnitAnkiCard`.
- `rating`: `again` | `hard` | `good` | `easy`.
- `previous_state`, `next_state`: State transition.
- `previous_interval_days`, `next_interval_days`: Interval transition.
- `previous_ease_factor`, `next_ease_factor`: Ease transition.
- `response_time_ms`: Optional client response time.
- `reviewed_at`: Review timestamp.

## 3. Content Models

### Vocabulary (`apps.vocabulary.models.Word`)
- `j_word`: Japanese word (Kanji/Kana).
- `phonetic`: Reading (Furigana).
- `mean`: JSON value containing definitions and examples.
- `level`: JLPT Level.
- `synsets`: JSON synonyms.

### Grammar (`apps.grammar.models.Grammar`)
- `title`: Grammar structure title.
- `structure`: Usage pattern.
- `mean`: Meaning.
- `level`: JLPT Level integer (5-1).
- `examples`: JSON array of example sentences.

### Kanji (`apps.kanjis.models.Kanji`)
- `kanji`: Character.
- `on`: Onyomi readings.
- `kun`: Kunyomi readings.
- `mean`: Meaning.
- `level`: JLPT Level integer.
- `examples`: JSON examples.

### Examples (`apps.examples.models.Example`)
- `content`: Japanese sentence.
- `mean`: Vietnamese meaning.
- `trans`: Transcription/Romaji.

## 4. Relationships (Junction Tables)
Due to data import structure, relationships are often stored as junction tables linking IDs:
- `UnitWordDetail`: Links `Unit` <-> `Word`.
- `UnitGrammarDetail`: Links `Unit` <-> `Grammar`.
- `UnitKanjiDetail`: Links `Unit` <-> `Kanji`.
