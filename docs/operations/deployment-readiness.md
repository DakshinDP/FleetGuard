# Deployment readiness

## Current state

- Local app source and Compose definition are in this repository. `docker compose config --quiet` parsed successfully.
- The containers have not started: this Windows session cannot access WSL or Docker Desktop's helper service, so the Linux engine pipe is unavailable.
- No FleetGuard repository was found in the connected GitHub account. GitHub CLI is not installed, and the browser is waiting at GitHub sign-in for the account owner.
- The AWS CLI identity check returned no usable credentials in this session. Terraform is not installed.
- `infra/terraform-compose/` now describes an end-to-end single-instance AWS demo for the complete Compose stack. It is not production architecture: one instance, HTTP, local data volumes, no managed database/HA/backup. It requires a trusted CIDR, AWS credentials and a reviewed cost plan before apply.
- `infra/terraform/` remains a separate API-only ECS starter and expects pre-created networking and PostgreSQL, Kafka, ClickHouse and Redis endpoints.

## Local run

1. Start Docker Desktop under the signed-in Windows account and wait until the **Linux engine** is running.
2. From the project root run `docker compose up --build -d`.
3. Check `docker compose ps`; open the dashboard at `http://localhost:3000` and log in with the local demo account shown in the root README.
4. Review logs with `docker compose logs -f api worker simulator`; stop with `docker compose down`.
5. Before sharing the service outside localhost, replace all `.env` demo values and add TLS and a production identity provider.

## Full cloud deployment decision

The single-instance AWS plan is now concrete enough to inspect, but applying it still creates a public IPv4 EC2 host, an encrypted 100 GB gp3 volume, an S3 bucket and running containers. Select the AWS region and monthly spend limit, confirm the trusted client CIDR (store it locally in `terraform.tfvars`, not in chat), and authenticate the AWS CLI/SSO on the host before apply. Cloud creation was not attempted because this session has no usable AWS identity and the monthly budget/CIDR were unspecified.

Do not send AWS access keys in chat. Sign in through the AWS CLI/SSO on the host, then verify locally with `aws sts get-caller-identity`. The deployment should proceed only after reviewing the complete Terraform plan and its cost-bearing resources.
