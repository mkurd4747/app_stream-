output "instance_id" {
  description = "EC2 instance identifier."
  value       = aws_instance.api.id
}

output "public_ip" {
  description = "Current public IP. It can change after an EC2 stop/start."
  value       = aws_instance.api.public_ip
}

output "api_docs_url" {
  description = "Swagger documentation URL, accessible only from allowed_cidr."
  value       = "http://${aws_instance.api.public_ip}:8000/docs"
}

output "session_manager_command" {
  description = "AWS CLI command for connecting without an inbound SSH rule."
  value       = "aws ssm start-session --target ${aws_instance.api.id} --region ${var.aws_region}"
}
