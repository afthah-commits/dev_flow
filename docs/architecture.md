# Architecture

## Overview
DevFlow is built using a modern, scalable client-server architecture separating the React frontend and FastAPI backend.

## Frontend Architecture
- **Framework:** React + Vite
- **Language:** TypeScript
- **State Management:** React Context (for Authentication) - avoiding Redux to maintain simplicity for Phase 1.
- **Styling:** Tailwind CSS v4 for rapid UI development and consistent design system.
- **Routing:** React Router v6.
- **API Client:** Axios instance with automatic JWT token injection and centralized configuration.

## Backend Architecture
- **Framework:** FastAPI
- **Language:** Python
- **Database ORM:** SQLAlchemy 2.0 with Alembic for migrations.
- **Authentication:** JWT (JSON Web Tokens) with Passlib (bcrypt) for secure password hashing.
- **Design Pattern:** Layered architecture
  - `api/`: Route handlers and controllers.
  - `core/`: Configuration, security, and application-level settings.
  - `db/`: Database session management and base classes.
  - `models/`: SQLAlchemy models mapping to database tables.
  - `schemas/`: Pydantic models for request validation and response serialization.

## Security Decisions
- Passwords are never stored in plaintext (hashed using bcrypt).
- JWT tokens are used for stateless authentication.
- Secrets are managed via `.env` files and never committed to version control.
- CORS is configured to only allow requests from the designated frontend URL.
- UUIDs are used for primary user identifiers to prevent sequential enumeration.

## Future Scalability Considerations
- The modular backend structure allows adding complex services (AI, Github Integration) easily.
- Database models can be easily expanded for workspaces and projects.
- The UI component system (`src/components/ui`) acts as a foundation for a fully-fledged design system.
