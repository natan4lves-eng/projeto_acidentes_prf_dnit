# ==========================================
# IAM ROLE — GLUE EXECUTION ROLE
# ==========================================

# Trust policy: permite que o serviço AWS Glue assuma esta role
data "aws_iam_policy_document" "glue_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue_role" {
  name               = "${var.project_name}-glue-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume_role.json
  description        = "Role de execução dos Glue Jobs do projeto ${var.project_name}"
}

# ==========================================
# POLICY 1 — AWS Glue Service Role (managed)
# Permissões base do Glue: Catalog, logs, métricas, etc.
# ==========================================
resource "aws_iam_role_policy_attachment" "glue_policy" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# ==========================================
# POLICY 2 — S3: Acesso aos buckets do projeto
# Leitura dos scripts, leitura/escrita no datalake, acesso ao temp
# ==========================================
data "aws_iam_policy_document" "glue_s3" {
  # Listar os buckets do projeto
  statement {
    sid    = "ListBuckets"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = [
      aws_s3_bucket.glue_assets.arn,
      aws_s3_bucket.datalake.arn,
      "arn:aws:s3:::temp-${data.aws_caller_identity.current.account_id}", # bucket temp do Athena CTAS
    ]
  }

  # Ler scripts e arquivos extras (utils.py, etc.)
  statement {
    sid    = "ReadGlueAssets"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
    ]
    resources = [
      "${aws_s3_bucket.glue_assets.arn}/*",
    ]
  }

  # Ler e escrever no datalake (Bronze, Silver, Gold, raw)
  statement {
    sid    = "ReadWriteDatalake"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      "${aws_s3_bucket.datalake.arn}/*",
    ]
  }

  # Acesso total ao bucket temp (TempDir do Glue + temp do Athena CTAS)
  statement {
    sid    = "ReadWriteTemp"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]
    resources = [
      "${aws_s3_bucket.glue_assets.arn}/temp/*",
      "arn:aws:s3:::temp-${data.aws_caller_identity.current.account_id}/*",
    ]
  }
}

resource "aws_iam_policy" "glue_s3_policy" {
  name        = "${var.project_name}-glue-s3-policy"
  description = "Permissões S3 para os Glue Jobs do ${var.project_name}"
  policy      = data.aws_iam_policy_document.glue_s3.json
}

resource "aws_iam_role_policy_attachment" "glue_s3_policy" {
  role       = aws_iam_role.glue_role.name
  policy_arn = aws_iam_policy.glue_s3_policy.arn
}

# ==========================================
# POLICY 3 — Athena: Executar queries (read_table + ingest_to_iceberg usam Athena)
# ==========================================
data "aws_iam_policy_document" "glue_athena" {
  statement {
    sid    = "AthenaQueryExecution"
    effect = "Allow"
    actions = [
      "athena:StartQueryExecution",
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:StopQueryExecution",
      "athena:ListQueryExecutions",
      "athena:GetWorkGroup",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "glue_athena_policy" {
  name        = "${var.project_name}-glue-athena-policy"
  description = "Permissões Athena para os Glue Jobs do ${var.project_name}"
  policy      = data.aws_iam_policy_document.glue_athena.json
}

resource "aws_iam_role_policy_attachment" "glue_athena_policy" {
  role       = aws_iam_role.glue_role.name
  policy_arn = aws_iam_policy.glue_athena_policy.arn
}

# ==========================================
# POLICY 4 — Glue Catalog: CRUD de databases e tabelas
# Necessário para criar/atualizar tabelas nas camadas Bronze, Silver e Gold
# ==========================================
data "aws_iam_policy_document" "glue_catalog" {
  statement {
    sid    = "GlueCatalogFullAccess"
    effect = "Allow"
    actions = [
      "glue:CreateDatabase",
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:UpdateDatabase",
      "glue:CreateTable",
      "glue:UpdateTable",
      "glue:GetTable",
      "glue:GetTables",
      "glue:DeleteTable",
      "glue:BatchDeleteTable",
      "glue:GetPartition",
      "glue:GetPartitions",
      "glue:CreatePartition",
      "glue:BatchCreatePartition",
      "glue:UpdatePartition",
      "glue:DeletePartition",
      "glue:BatchDeletePartition",
    ]
    resources = [
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:catalog",
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${var.project_name}_bronze",
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${var.project_name}_silver",
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/${var.project_name}_gold",
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.project_name}_bronze/*",
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.project_name}_silver/*",
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/${var.project_name}_gold/*",
    ]
  }
}

resource "aws_iam_policy" "glue_catalog_policy" {
  name        = "${var.project_name}-glue-catalog-policy"
  description = "Permissões no Glue Data Catalog para Bronze, Silver e Gold"
  policy      = data.aws_iam_policy_document.glue_catalog.json
}

resource "aws_iam_role_policy_attachment" "glue_catalog_policy" {
  role       = aws_iam_role.glue_role.name
  policy_arn = aws_iam_policy.glue_catalog_policy.arn
}

# ==========================================
# POLICY 5 — Glue Jobs: permite que um job dispare outro (executar_glue_job no utils.py)
# Bronze dispara Silver, Silver dispara Gold
# ==========================================
data "aws_iam_policy_document" "glue_trigger_jobs" {
  statement {
    sid    = "StartGlueJobs"
    effect = "Allow"
    actions = [
      "glue:StartJobRun",
      "glue:GetJobRun",
      "glue:GetJob",
    ]
    resources = [
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:job/glue_processar_bronze",
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:job/glue_processar_silver",
      "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:job/glue_processar_gold",
    ]
  }
}

resource "aws_iam_policy" "glue_trigger_jobs_policy" {
  name        = "${var.project_name}-glue-trigger-jobs-policy"
  description = "Permite que um Glue Job dispare outro (encadeamento Bronze→Silver→Gold)"
  policy      = data.aws_iam_policy_document.glue_trigger_jobs.json
}

resource "aws_iam_role_policy_attachment" "glue_trigger_jobs_policy" {
  role       = aws_iam_role.glue_role.name
  policy_arn = aws_iam_policy.glue_trigger_jobs_policy.arn
}

# ==========================================
# POLICY 6 — CloudWatch Logs: gravação de logs dos jobs
# ==========================================
data "aws_iam_policy_document" "glue_logs" {
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
      "logs:DescribeLogGroups",
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws-glue/*",
    ]
  }
}

resource "aws_iam_policy" "glue_logs_policy" {
  name        = "${var.project_name}-glue-logs-policy"
  description = "Permissão de escrita de logs no CloudWatch para os Glue Jobs"
  policy      = data.aws_iam_policy_document.glue_logs.json
}

resource "aws_iam_role_policy_attachment" "glue_logs_policy" {
  role       = aws_iam_role.glue_role.name
  policy_arn = aws_iam_policy.glue_logs_policy.arn
}
