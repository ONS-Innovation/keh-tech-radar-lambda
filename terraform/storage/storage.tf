resource "aws_s3_bucket" "tech_audit_data_bucket" {
  bucket = "${var.domain}-${var.service_subdomain}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "enabled" {
  bucket = aws_s3_bucket.tech_audit_data_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "blocked" {
  bucket = aws_s3_bucket.tech_audit_data_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "encrypt_by_default" {
  bucket = aws_s3_bucket.tech_audit_data_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_policy" "allow_access_from_frontend" {
  bucket = aws_s3_bucket.tech_audit_data_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.tech_audit_data_bucket.arn}/*"
        Condition = {
          StringLike = {
            "aws:Referer" = [
              "http://localhost:3000/*",
              "https://tech-radar.sdp-dev.aws.onsdigital.uk/*"
            ]
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_cors_configuration" "cors_config" {
  bucket = aws_s3_bucket.tech_audit_data_bucket.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = [
      "http://localhost:3000",
      "https://tech-radar.sdp-dev.aws.onsdigital.uk"
    ]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}