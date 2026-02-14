# Business Rules

## 1. Authentication & Users
- **Identity:** Users are identified by Email. Username is not used.
- **Roles:**
  - `ADMIN`: Full access to Django Admin and all API endpoints.
  - `USER`: Standard access to learning resources.
- **Social Login:** Accounts created via Google/Facebook auto-merge if email matches.

## 2. Learning Content
- **Hierarchy:** Course -> Lesson -> Unit -> Content (Vocab/Grammar/Kanji).
- **Access Control:** Currently, all registered users can access all levels (N5-N1). *Subject to change in future phases.*

## 3. Progression
- **Tracking:** Progress is tracked per `Unit`.
- **Streak:** Completing a unit increments/maintains the daily streak.
- **Spaced Repetition:** *Planned feature, current implementation uses simple completion tracking.*

## 4. Content Restrictions
- **Example Sentences:** Linked to specific Words/Grammar/Kanji. One item can have multiple examples.
