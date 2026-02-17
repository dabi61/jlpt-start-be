# Business Rules

## 1. Authentication & Users
- **Identity:** Users are identified by Email. Username is not used.
- **Roles:**
  - `ADMIN`: Full access to Django Admin and all API endpoints.
  - `USER`: Standard access to learning resources.
- **Social Login:** Accounts created via Google/Facebook auto-merge if email matches.

## 2. Learning Content
- **Hierarchy:** Course -> Lesson -> Unit -> Content (Vocab/Grammar/Kanji).
- **Access Control (Read):** Currently, all registered users can access all levels (N5-N1). *Subject to change in future phases.*
- **Access Control (Write):** Content/datasets are managed by admins.
  - Regular users can `GET` learning resources.
  - Only admins can `POST/PUT/PATCH/DELETE` content datasets (Vocabulary/Grammar/Kanji/Examples, N1..N5 datasets, Lessons/Units).

## 3. Progression
- **Tracking:** Progress is tracked per `Unit`.
- **Streak:** Completing a unit increments/maintains the daily streak.
  - Completion signal: `UserUnitProgress.progress >= 100` (percentage).
  - If user completes multiple units in the same day, streak does not increment multiple times.
  - Streak update:
    - If `last_study_date == today`: keep `streak` unchanged.
    - If `last_study_date == yesterday`: `streak += 1`.
    - Else (or null): `streak = 1`.
    - Always set `last_study_date = today` on first completion that day.
- **Spaced Repetition:** *Planned feature, current implementation uses simple completion tracking.*

## 4. Content Restrictions
- **Example Sentences:** Linked to specific Words/Grammar/Kanji. One item can have multiple examples.
