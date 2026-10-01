output "dashboard_url" {
  description = "HTTP dashboard, restricted to allowed_cidr by the security group"
  value       = "http://${aws_instance.demo.public_ip}/"
}

output "instance_id" {
  value = aws_instance.demo.id
}

output "demo_email" {
  value = "demo@fleetguard.local"
}

output "demo_password_parameter" {
  description = "Retrieve the random demo password with AWS SSM GetParameter --with-decryption"
  value       = "/fleetguard/${random_id.suffix.hex}/demo-password"
}

output "bundle_bucket" {
  value = aws_s3_bucket.bundle.bucket
}
