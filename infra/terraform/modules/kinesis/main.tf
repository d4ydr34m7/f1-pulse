resource "aws_kinesis_stream" "telemetry_stream" {
  name = var.stream_name

  # Enterprise standard: On-demand capacity prevents runaway costs for spiky workloads
  stream_mode_details {
    stream_mode = "ON_DEMAND"
  }

  tags = {
    Name        = var.stream_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}