data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}
data "aws_ssm_parameter" "ubuntu_ami" {
  name = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

resource "aws_vpc" "demo" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "${var.name_prefix}-vpc" }
}

resource "aws_internet_gateway" "demo" {
  vpc_id = aws_vpc.demo.id
  tags   = { Name = "${var.name_prefix}-igw" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.demo.id
  cidr_block              = var.subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  tags                    = { Name = "${var.name_prefix}-public" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.demo.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.demo.id
  }
  tags = { Name = "${var.name_prefix}-public" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "bundle" {
  bucket        = "${var.name_prefix}-${random_id.suffix.hex}"
  force_destroy = false
}

resource "aws_s3_bucket_public_access_block" "bundle" {
  bucket                  = aws_s3_bucket.bundle.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bundle" {
  bucket = aws_s3_bucket.bundle.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_s3_object" "bundle" {
  bucket       = aws_s3_bucket.bundle.id
  key          = "fleetguard-ai.zip"
  source       = "${path.module}/../../../fleetguard-ai.zip"
  etag         = filemd5("${path.module}/../../../fleetguard-ai.zip")
  content_type = "application/zip"
}

resource "aws_security_group" "demo" {
  name        = "${var.name_prefix}-${random_id.suffix.hex}"
  description = "FleetGuard demo HTTP only from the configured trusted client CIDR"
  vpc_id      = aws_vpc.demo.id

  ingress {
    description = "Dashboard HTTP; restrict allowed_cidr to a trusted /32"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_iam_role" "instance" {
  name = "${var.name_prefix}-${random_id.suffix.hex}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ec2.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "bundle_and_demo_password" {
  name = "fleetguard-bootstrap"
  role = aws_iam_role.instance.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:GetObject"], Resource = ["${aws_s3_bucket.bundle.arn}/${aws_s3_object.bundle.key}"] },
      { Effect = "Allow", Action = ["ssm:PutParameter", "ssm:GetParameter"], Resource = ["arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/fleetguard/${random_id.suffix.hex}/demo-password"] }
    ]
  })
}

resource "aws_iam_instance_profile" "instance" {
  name = "${var.name_prefix}-${random_id.suffix.hex}"
  role = aws_iam_role.instance.name
}

resource "aws_instance" "demo" {
  ami                         = data.aws_ssm_parameter.ubuntu_ami.value
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.demo.id]
  iam_instance_profile        = aws_iam_instance_profile.instance.name
  associate_public_ip_address = true
  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    aws_region   = var.aws_region
    bucket       = aws_s3_bucket.bundle.bucket
    object_key   = aws_s3_object.bundle.key
    parameter    = "/fleetguard/${random_id.suffix.hex}/demo-password"
    bundle_etag  = aws_s3_object.bundle.etag
  })

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_disk_gb
    encrypted             = true
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  depends_on = [
    aws_iam_role_policy_attachment.ssm,
    aws_iam_role_policy.bundle_and_demo_password,
    aws_s3_bucket_public_access_block.bundle,
    aws_s3_bucket_server_side_encryption_configuration.bundle,
    aws_route_table_association.public
  ]

  tags = { Name = "${var.name_prefix}-${random_id.suffix.hex}" }
}
