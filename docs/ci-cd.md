# Continuous Integration and Deployment

## CI Pipeline
The repository is configured with a GitHub Actions workflow (`.github/workflows/ci.yml`).

The pipeline runs on every push and pull request and performs:
- Python Backend tests via `pytest`
- Typescript type checking for Frontend (`tsc --noEmit`)
- Frontend production build verification (`npm run build`)

The pipeline prevents merging breaking changes.

## Deployment Strategy
Automatic continuous deployment (CD) is not implemented by default. You can extend the GitHub Action to push the Docker images to a registry (e.g., GHCR, ECR) and trigger a deployment to your target environment.
