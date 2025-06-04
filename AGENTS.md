# AGENT Instructions for AI Document Processor

This repository hosts a FastAPI backend with a Next.js frontend for processing PDF documents using GPT‑4o Vision. The goal of this file is to help future Codex agents understand how to work with the project.

## Repository layout
- `backend/` – FastAPI application and worker code.
- `frontend/` – Next.js 15 frontend application.
- `scripts/` – helper scripts for starting the app locally.
- `docs/` – additional documentation and screenshots.

## Development environment
1. **Python 3.11+ and Node 18+** are required.
2. Copy `.env.example` to `.env` and add your `OPENAI_API_KEY`.
3. Run `./scripts/dev.sh` to launch backend and frontend without Docker.
   - This script checks ports automatically and installs dependencies if missing.
4. For a Docker based setup run `./start-local.sh` or `docker-compose -f docker-compose.local.yml up --build`.

## Style guidelines
- **Python**: format with `black` and lint with `flake8`.
- **TypeScript/JavaScript**: run `npm run lint` and `npm run format` (ESLint + Prettier).
- Follow the commit message examples in `CONTRIBUTING.md` (e.g., `feat:`, `fix:`). Conventional commits keep history readable.

## Testing
- Backend tests run with `pytest`. There are currently no unit tests, but add them for new features.
- Frontend or end‑to‑end tests can be executed with Puppeteer: `node test/verify-app.js`.
- When adding tests, ensure `pytest` and `npm test` succeed before committing.

## Useful commands
```bash
# Start dev mode
./scripts/dev.sh

# Run the Docker stack
./start-local.sh      # or docker-compose -f docker-compose.local.yml up

# Format backend code
cd backend && black app/ && flake8 app/

# Format frontend code
cd frontend && npm run lint && npm run format
```

## Notes on design choices
- **FastAPI** was chosen for the backend because it provides automatic validation and async support, following recommendations from the official docs [`fastapi.tiangolo.com`](https://fastapi.tiangolo.com/).
- **Next.js 15** is used on the frontend for modern React routing and server components as suggested in the docs at [`nextjs.org`](https://nextjs.org/).
- Docker support enables consistent local and production deployments.

Keep this file updated whenever workflows change so future agents understand how to run and modify the application.
