# AWS single-instance demo deployment

This is a low-complexity cloud demo path for the **entire Compose project**. It stores the source bundle in a private, encrypted S3 bucket; starts Ubuntu 24.04 on EC2; installs Docker Compose; generates random database/JWT/demo-password secrets on the instance; and starts the Compose stack. The generated demo password is written to a SecureString parameter. The instance is reachable over HTTP port 80 only from `allowed_cidr`. SSH is not opened; Systems Manager is the administration path.

It is a demo deployment, not production architecture. One instance and local container volumes are single points of failure; there is no TLS, managed database, multi-AZ recovery, backup schedule or automated GitHub deployment. The 100K vehicles are seeded but target event throughput is not claimed. Review the full plan and expected monthly charges before applying.

## Inputs

- `aws_region`: defaults to `ap-south-1`.
- `vpc_cidr` and `subnet_cidr`: an isolated VPC and public subnet created by this module.
- `allowed_cidr`: trusted client IPv4 CIDR, preferably a single `/32`. No default is provided.
- `instance_type`: defaults to `t3.xlarge`; choose a size after reviewing budget and workload.
- `root_disk_gb`: encrypted gp3 volume, defaults to 100 GB.

## Apply

Create a local `terraform.tfvars` in this folder with the network IDs and restricted CIDR. Do not put application secrets there. The module packages `../../../fleetguard-ai.zip`; regenerate that archive from the project before applying. Sign into AWS with an authorized profile/SSO session, install Terraform 1.6+, then:

```sh
terraform init
terraform plan -out fleetguard.plan
terraform show fleetguard.plan
terraform apply fleetguard.plan
```

After cloud-init completes, open the `dashboard_url` output. Retrieve the random demo password using the parameter name shown by `demo_password_parameter`:

```sh
aws ssm get-parameter --name /fleetguard/<suffix>/demo-password --with-decryption --query Parameter.Value --output text
```

Check bootstrap logs in Systems Manager or `/var/log/fleetguard-bootstrap.log`. To redeploy a changed bundle, regenerate the ZIP and run `terraform apply` after reviewing the plan. `terraform destroy` removes the instance, but the S3 bundle bucket has deletion protection through `force_destroy = false`; review and remove the artifact bucket deliberately after the instance is gone.
