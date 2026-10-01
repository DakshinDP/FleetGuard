output "ecs_cluster_name" { value = aws_ecs_cluster.fleetguard.name }
output "ecs_service_name" { value = aws_ecs_service.api.name }
output "log_group" { value = aws_cloudwatch_log_group.api.name }
