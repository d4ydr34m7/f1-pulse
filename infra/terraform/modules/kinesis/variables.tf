variable "stream_name" {
  description = "The name of the Kinesis data stream"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)"
  type        = string
}