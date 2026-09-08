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