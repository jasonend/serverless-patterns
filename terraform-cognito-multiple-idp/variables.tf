variable "cognito_pool_name" {
    type = string
    default = null
    nullable = true
}

variable "saml_providers" {
  type     = map(any)
  default  = null
  nullable = true
}

variable "oidc_providers" {
  type     = map(any)
  default  = null
  nullable = true
}