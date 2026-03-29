variable "aws_region" {
  description = "Região AWS onde os recursos serão criados"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefixo do projeto, usado para nomear todos os recursos"
  type        = string
  default     = "datalake-empresa"
}
