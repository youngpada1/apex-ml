provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

# SNS Topic for billing alerts
resource "aws_sns_topic" "billing_alerts" {
  provider = aws.us_east_1
  name     = "apex-ml-billing-alerts-${var.environment}"
  
  tags = {
    Environment = var.environment
    Project     = "apex-ml"
  }
}

resource "aws_sns_topic_subscription" "billing_email" {
  provider  = aws.us_east_1
  topic_arn = aws_sns_topic.billing_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Alarm for $2 spending (warning)
resource "aws_cloudwatch_metric_alarm" "billing_alarm_2_dollars" {
  provider            = aws.us_east_1
  alarm_name          = "billing-alarm-10-dollars-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600  # 6 hours
  statistic           = "Maximum"
  threshold           = 2.00
  alarm_description   = "Alert when spending exceeds $10 in ${var.environment}"
  alarm_actions       = [aws_sns_topic.billing_alerts.arn]

  dimensions = {
    Currency = "USD"
  }
  
  tags = {
    Environment = var.environment
  }
}

# Alarm for $10 spending (critical)
resource "aws_cloudwatch_metric_alarm" "billing_alarm_10_dollars" {
  provider            = aws.us_east_1
  alarm_name          = "billing-alarm-50-dollars-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600
  statistic           = "Maximum"
  threshold           = 10.00
  alarm_description   = "URGENT: Spending exceeds $50 in ${var.environment}!"
  alarm_actions       = [aws_sns_topic.billing_alerts.arn]

  dimensions = {
    Currency = "USD"
  }
  
  tags = {
    Environment = var.environment
  }
}