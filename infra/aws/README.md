# AWS-ready telemetry deployment

This Terraform configuration prepares a small learning deployment of
`mkurd47/telemetry-stream-api:1.0` on one Amazon Linux 2023 EC2 instance.

It creates:

- one EC2 instance in the account's default VPC;
- a security group allowing API port 8000 only from `allowed_cidr`;
- an EC2 IAM role and instance profile for AWS Systems Manager;
- an encrypted 10 GiB root EBS volume;
- Docker, the telemetry API container, and a persistent Docker volume.

It deliberately does not open SSH. Connect through AWS Systems Manager Session
Manager. This is a learning architecture, not a highly available production
design. SQLite and a single EC2 instance remain single points of failure.

## Before applying


1. Confirm the authorized AWS account and profile:

   ```powershell
   aws sts get-caller-identity
   aws configure list
   ```

2. Create an AWS budget or billing alert.
3. Review current EC2, EBS, public IPv4, and data-transfer pricing.
4. Confirm the account has a default VPC and default subnets.
5. Confirm `mkurd47/telemetry-stream-api:1.0` is public and pulls successfully.
6. Determine your current public IPv4 address and express it as `/32`.

Do not store AWS access keys in any Terraform file.

## Configure

From the repository root:

```powershell
Copy-Item infra\aws\terraform.tfvars.example infra\aws\terraform.tfvars
```

Edit `infra\aws\terraform.tfvars` and replace the example `allowed_cidr` with
your actual public IPv4 address followed by `/32`. The configuration rejects
`0.0.0.0/0` for inbound API access.

`terraform.tfvars` is ignored by Git because it contains environment-specific
settings. It must not contain passwords or AWS credentials.

## Validate without creating resources

```powershell
Set-Location infra\aws
terraform fmt -recursive
terraform init
terraform validate
terraform plan -out=tfplan
```

`terraform init` downloads the provider and creates `.terraform.lock.hcl`.
Commit `.terraform.lock.hcl`; do not commit `.terraform`, state files,
`tfplan`, or `terraform.tfvars`.

Read the entire plan before deciding whether to deploy. A plan does not create
the EC2 instance.

## Deploy only when authorized

```powershell
terraform apply tfplan
terraform output
```

The cloud-init script installs Docker and starts the public Docker Hub image.
Initial startup may take several minutes. The output `api_docs_url` is
accessible only from the configured CIDR.

## Connect through Session Manager

Use the generated command:

```powershell
terraform output -raw session_manager_command
```

Run that command after confirming the instance is registered with Systems
Manager. On the instance, inspect the application with:

```bash
sudo docker ps
sudo docker logs telemetry-stream-api
```

## Destroy to stop ongoing resource charges

When the learning deployment is no longer required:

```powershell
terraform plan -destroy -out=destroy.tfplan
terraform apply destroy.tfplan
```

Confirm in AWS Billing and the EC2 console that no unintended instances,
volumes, snapshots, or public IPv4 resources remain. Destroying the instance
also deletes the root volume and the SQLite data stored within it.

## Add the folder to Git

Return to the repository root:

```powershell
git add infra\aws
git status
git diff --staged
git commit -m "Add AWS deployment infrastructure"
git push -u origin HEAD
```
