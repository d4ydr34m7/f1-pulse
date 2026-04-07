# 1. Build the Buffer
module "kinesis" {
  source      = "../../modules/kinesis"
  environment = "dev"
  stream_name = "f1-pulse-dev-stream"
}

# 2. Build the Database (Pivot to DynamoDB)
module "dynamodb" {
  source      = "../../modules/dynamodb"
  environment = "dev"
  table_name  = "f1-live-telemetry"
}

# 3. Build the Processor and Wire them together
module "lambda" {
  source                = "../../modules/lambda"
  environment           = "dev"
  source_file_path      = "../../../../backend/process_telemetry.py"
  kinesis_stream_arn    = module.kinesis.stream_arn
  dynamodb_table_name   = module.dynamodb.table_name
}