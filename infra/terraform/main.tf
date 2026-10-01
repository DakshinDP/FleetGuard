resource "aws_ecs_cluster" "fleetguard" {
  name = "fleetguard"
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
resource "aws_cloudwatch_log_group" "api" {
  name = "/ecs/fleetguard/api"
  retention_in_days = 30
}
resource "aws_iam_role" "execution" {
  name = "fleetguard-ecs-execution"
  assume_role_policy = jsonencode({Version="2012-10-17",Statement=[{Effect="Allow",Principal={Service="ecs-tasks.amazonaws.com"},Action="sts:AssumeRole"}]})
}
resource "aws_iam_role_policy_attachment" "execution" {
  role = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
resource "aws_iam_role_policy" "read_secret" {
  role = aws_iam_role.execution.id
  policy = jsonencode({Version="2012-10-17",Statement=[{Effect="Allow",Action=["secretsmanager:GetSecretValue"],Resource=[var.secret_arn]}]})
}
resource "aws_ecs_task_definition" "api" {
  family = var.service_name
  requires_compatibilities = ["FARGATE"]
  network_mode = "awsvpc"
  cpu = "512"
  memory = "1024"
  execution_role_arn = aws_iam_role.execution.arn
  task_role_arn = aws_iam_role.execution.arn
  container_definitions = jsonencode([{
    name="api", image=var.container_image, essential=true,
    command = ["uvicorn", "fleetguard.api:app", "--host", "0.0.0.0", "--port", "8000"],
    portMappings = [{containerPort = 8000, protocol = "tcp"}],
    secrets = [
      {name = "POSTGRES_DSN", valueFrom = "${var.secret_arn}:POSTGRES_DSN::"},
      {name = "JWT_SECRET", valueFrom = "${var.secret_arn}:JWT_SECRET::"},
      {name = "DEMO_PASSWORD", valueFrom = "${var.secret_arn}:DEMO_PASSWORD::"}
    ],
    environment=[
      {name="CLICKHOUSE_HOST",value=var.clickhouse_host},
      {name="REDIS_URL",value=var.redis_url},
      {name="KAFKA_BOOTSTRAP_SERVERS",value=var.kafka_bootstrap_servers}
    ],
    healthCheck = {command = ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')\""], interval = 30, timeout = 5, retries = 3, startPeriod = 20},
    logConfiguration = {logDriver = "awslogs", options = {"awslogs-group" = aws_cloudwatch_log_group.api.name, "awslogs-region" = var.aws_region, "awslogs-stream-prefix" = "api"}}
  }])
}
resource "aws_ecs_service" "api" {
  name = var.service_name
  cluster = aws_ecs_cluster.fleetguard.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count = var.desired_count
  launch_type = "FARGATE"
  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent = 200
  network_configuration {
    subnets = var.subnet_ids
    security_groups = var.security_group_ids
    assign_public_ip = false
  }
}
