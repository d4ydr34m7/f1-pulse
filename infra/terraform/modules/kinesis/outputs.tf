output "stream_arn" {
  value       = aws_kinesis_stream.telemetry_stream.arn
  description = "The ARN of the Kinesis stream, needed for Lambda trigger"
}

output "stream_name" {
  value       = aws_kinesis_stream.telemetry_stream.name
  description = "The name of the Kinesis stream"
}