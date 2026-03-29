terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ==========================================
# DATA SOURCE: Account ID atual
# ==========================================
data "aws_caller_identity" "current" {}

# ==========================================
# S3 — BUCKET DE ASSETS DO GLUE
# ==========================================
resource "aws_s3_bucket" "glue_assets" {
  bucket = "${var.project_name}-glue-assets-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "glue_assets" {
  bucket = aws_s3_bucket.glue_assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "glue_assets" {
  bucket = aws_s3_bucket.glue_assets.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "glue_assets" {
  bucket                  = aws_s3_bucket.glue_assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ==========================================
# S3 — BUCKET DO DATALAKE (Bronze/Silver/Gold)
# ==========================================
resource "aws_s3_bucket" "datalake" {
  bucket = "${var.project_name}-datalake-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "datalake" {
  bucket = aws_s3_bucket.datalake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "datalake" {
  bucket = aws_s3_bucket.datalake.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "datalake" {
  bucket                  = aws_s3_bucket.datalake.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Prefixos lógicos das camadas no datalake
resource "aws_s3_object" "prefix_bronze" {
  bucket  = aws_s3_bucket.datalake.id
  key     = "bronze/"
  content = ""
}

resource "aws_s3_object" "prefix_silver" {
  bucket  = aws_s3_bucket.datalake.id
  key     = "silver/"
  content = ""
}

resource "aws_s3_object" "prefix_gold" {
  bucket  = aws_s3_bucket.datalake.id
  key     = "gold/"
  content = ""
}

# ==========================================
# S3 — UPLOAD DOS SCRIPTS GLUE
# ==========================================
resource "aws_s3_object" "glue_script_utils" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = "scripts/utils.py"
  source = "../scripts/utils.py"
  etag   = filemd5("../scripts/utils.py")
}

resource "aws_s3_object" "glue_script_bronze" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = "scripts/01_glue_processa_bronze.py"
  source = "../scripts/01_glue_processa_bronze.py"
  etag   = filemd5("../scripts/01_glue_processa_bronze.py")
}

resource "aws_s3_object" "glue_script_silver" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = "scripts/02_glue_processa_silver.py"
  source = "../scripts/02_glue_processa_silver.py"
  etag   = filemd5("../scripts/02_glue_processa_silver.py")
}

resource "aws_s3_object" "glue_script_gold" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = "scripts/03_glue_processa_gold.py"
  source = "../scripts/03_glue_processa_gold.py"
  etag   = filemd5("../scripts/03_glue_processa_gold.py")
}

# ==========================================
# GLUE CATALOG — DATABASES
# ==========================================
resource "aws_glue_catalog_database" "bronze" {
  name = "${var.project_name}_bronze"
}

resource "aws_glue_catalog_database" "silver" {
  name = "${var.project_name}_silver"
}

resource "aws_glue_catalog_database" "gold" {
  name = "${var.project_name}_gold"
}

# ==========================================
# JOB DA CAMADA BRONZE
# ==========================================
resource "aws_glue_job" "processa_bronze" {
  name     = "glue_processar_bronze"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.glue_assets.id}/scripts/01_glue_processa_bronze.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--TempDir"                          = "s3://${aws_s3_bucket.glue_assets.id}/temp/"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-job-insights"              = "true"
    "--job-bookmark-option"              = "job-bookmark-disable"  # Bronze faz full overwrite
    "--extra-py-files"                   = "s3://${aws_s3_bucket.glue_assets.id}/scripts/utils.py"
    # Parâmetros de negócio — preencha conforme seu ambiente
    "--db_destino"       = aws_glue_catalog_database.bronze.name
    "--tb_destino"       = "tb_prf_ocorrencia"
    "--s3_path_origem"   = "s3://${aws_s3_bucket.datalake.id}/raw/"
    "--s3_path_destino"  = "s3://${aws_s3_bucket.datalake.id}/bronze/tb_prf_ocorrencia/"
  }

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 10
  max_retries       = 0
  timeout           = 60

  depends_on = [
    aws_s3_object.glue_script_bronze,
    aws_s3_object.glue_script_utils,
    aws_iam_role_policy_attachment.glue_policy,
    aws_iam_role_policy_attachment.glue_s3_policy,
    aws_iam_role_policy_attachment.glue_athena_policy,
  ]
}

# ==========================================
# JOB DA CAMADA SILVER
# ==========================================
resource "aws_glue_job" "processa_silver" {
  name     = "glue_processar_silver"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.glue_assets.id}/scripts/02_glue_processa_silver.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--TempDir"                          = "s3://${aws_s3_bucket.glue_assets.id}/temp/"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-job-insights"              = "true"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--extra-py-files"                   = "s3://${aws_s3_bucket.glue_assets.id}/scripts/utils.py"
    # Parâmetros de negócio
    "--db_origem"   = aws_glue_catalog_database.bronze.name
    "--tb_origem"   = "tb_prf_ocorrencia"
    "--db_destino"  = aws_glue_catalog_database.silver.name
    "--tb_destino"  = "tb_prf_ocorrencia_silver"
    "--s3_path"     = "s3://${aws_s3_bucket.datalake.id}/silver/tb_prf_ocorrencia/"
  }

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 10
  max_retries       = 0
  timeout           = 60

  depends_on = [
    aws_s3_object.glue_script_silver,
    aws_s3_object.glue_script_utils,
    aws_glue_job.processa_bronze,
    aws_iam_role_policy_attachment.glue_policy,
    aws_iam_role_policy_attachment.glue_s3_policy,
    aws_iam_role_policy_attachment.glue_athena_policy,
  ]
}

# ==========================================
# JOB DA CAMADA GOLD
# ==========================================
resource "aws_glue_job" "processa_gold" {
  name     = "glue_processar_gold"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.glue_assets.id}/scripts/03_glue_processa_gold.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--TempDir"                          = "s3://${aws_s3_bucket.glue_assets.id}/temp/"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-job-insights"              = "true"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--extra-py-files"                   = "s3://${aws_s3_bucket.glue_assets.id}/scripts/utils.py"
    # Parâmetros de negócio
    "--db_origem"           = aws_glue_catalog_database.silver.name
    "--tb_origem"           = "tb_prf_ocorrencia_silver"
    "--db_destino"          = aws_glue_catalog_database.gold.name
    "--tabela_destino_01"   = "dim_localizacao"
    "--tabela_destino_02"   = "dim_tempo"
    "--tabela_destino_03"   = "dim_clima"
    "--tabela_destino_04"   = "dim_causa_acidente"
    "--tabela_destino_05"   = "dim_pessoa"
    "--tabela_destino_06"   = "dim_veiculo"
    "--tabela_destino_07"   = "fato_acidentes"
    "--tabela_destino_08"   = "fato_envolvidos"
    "--s3_path"             = "s3://${aws_s3_bucket.datalake.id}/gold/"
  }

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 10
  max_retries       = 0
  timeout           = 120 # Gold é mais pesado — ajustado para 2h

  depends_on = [
    aws_s3_object.glue_script_gold,
    aws_s3_object.glue_script_utils,
    aws_glue_job.processa_silver,
    aws_iam_role_policy_attachment.glue_policy,
    aws_iam_role_policy_attachment.glue_s3_policy,
    aws_iam_role_policy_attachment.glue_athena_policy,
  ]
}
