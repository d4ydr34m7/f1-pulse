# 1. Zip the Python Code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = var.source_file_path
  output_path = "${path.module}/lambda_function.zip"
}

# 2. The Execution Role (Permissions)
resource "aws_iam_role" "lambda_exec_role" {
  name = "f1-pulse-${var.environment}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# 3. Policy: Allow reading from Kinesis and writing to DYNAMODB
resource "aws_iam_role_policy" "lambda_policy" {
  role = aws_iam_role.lambda_exec_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["kinesis:GetRecords", "kinesis:GetShardIterator", "kinesis:DescribeStream", "kinesis:ListStreams"]
        Effect   = "Allow"
        Resource = var.kinesis_stream_arn
      },
      {
        Action   = ["dynamodb:PutItem", "dynamodb:BatchWriteItem"]
        Effect   = "Allow"
        Resource = "*" 
      },
      {
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action   = ["dynamodb:PutItem", "dynamodb:BatchWriteItem"]
        Effect   = "Allow"
        Resource = "*" 
      },
      {
        Action   = ["cloudwatch:PutMetricData"]
        Effect   = "Allow"
        Resource = "*" 
      },
    ]
  })
}

# 4. The Lambda Function
resource "aws_lambda_function" "processor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "f1-pulse-${var.environment}-processor"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "process_telemetry.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.12"
  timeout          = 30 

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = var.dynamodb_table_name
    }
  }
}

# 5. The Kinesis Trigger (Event Source Mapping)
resource "aws_lambda_event_source_mapping" "kinesis_trigger" {
  event_source_arn  = var.kinesis_stream_arn
  function_name     = aws_lambda_function.processor.arn
  starting_position = "LATEST"
  batch_size        = 1000 
}