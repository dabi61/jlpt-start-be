# System Architecture Overview

## 1. Project Overview
**Project Name:** Nihongo Learning Backend
**Description:** Backend API for a Japanese language learning application (similar to Duolingo/Migii) supporting JLPT levels N5-N1.

## 2. Technology Stack

### Backend Core
- **Framework:** Django 5.0
- **Language:** Python 3.x
- **API:** Django Rest Framework (DRF) 3.14
- **Authentication:**
  - JWT (SimpleJWT)
  - OTP verification via email (registration flow)
  - Social providers are installed via allauth but not exposed as public API endpoints yet
- **Documentation:** DRF Spectacular (OpenAPI 3.0/Swagger)

### Database & Storage
- **Primary DB:** PostgreSQL 16
- **Caching & Broker:** Redis 7 (Alpine)

### Async Task Processing
- **Queue:** Celery 5.3
- **Broker:** Redis

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Server:** Gunicorn (Production), Manage.py (Dev)

## 3. Core Modules (Apps)

### User Management (`apps.users`)
- Custom User model (Email-based)
- JLPT Level tracking
- Learning streak & progress summary
- Profile management

### Learning Core (`apps.learning`)
- **Lessons:** Grouping of units (e.g., "Lesson 1: Greeting")
- **Units:** Specific learning modules (Vocab, Grammar, Kanji)
- **Progress:** Tracking completion of units per user

### Content Modules
- **Vocabulary (`apps.vocabulary`):** Words, meanings, synonyms, antonyms.
- **Grammar (`apps.grammar`):** Grammar points, structure, explanations.
- **Kanji (`apps.kanjis`):** Characters, onyomi/kunyomi, stroke order.
- **Examples (`apps.examples`):** Sentence examples linked to content.

## 4. Key Workflows

### Authentication
1. User registers via Email.
2. Server sends OTP and activates account after OTP verification.
3. Server issues JWT (Access + Refresh tokens) on login.
4. Access token used for API requests.

### Learning Flow
1. User fetches List of Lessons -> Units.
2. User studies a Unit (Vocab/Grammar/Kanji).
3. App submits progress -> `UserUnitProgress` updated.
4. User streak updated.
