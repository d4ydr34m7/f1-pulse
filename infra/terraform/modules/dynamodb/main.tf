resource "aws_dynamodb_table" "telemetry" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST" # Serverless on-demand pricing
  hash_key     = "Driver"
  range_key    = "Timestamp"

  attribute {
    name = "Driver"
    type = "S"
  }
  attribute {
    name = "Timestamp"
    type = "N" # Number (Unix Epoch)
  }

  # Automatically delete data older than 24 hours to save money
  ttl {
    attribute_name = "ExpirationTime"
    enabled        = true
  }

  tags = {
    Name        = var.table_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}