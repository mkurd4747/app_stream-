# app_stream-
This is an app stream 
## CI/CD

This project uses GitHub Actions to:

- Check Python formatting with Ruff
- Run linting with Ruff
- Check type hints with mypy
- Run pytest and coverage
- Build the Docker image
- Publish versioned images to Docker Hub
- Validate the AWS Terraform configuration

Docker image:

```text
mkurd47/tit-stream-api

## Monitoring

The API provides the following monitoring endpoints:

- `/health` checks whether the API is running.
- `/ready` checks whether the database is accessible.
- `/metrics` returns Prometheus-compatible request metrics.

Every response includes an `X-Request-ID` header. If the caller supplies an
`X-Request-ID`, the API preserves it. Otherwise, the API generates a unique ID.

The Docker image checks `/health` automatically to determine whether the
container is healthy.