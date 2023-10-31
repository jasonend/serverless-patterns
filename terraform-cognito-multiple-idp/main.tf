terraform {
    required_version = ">= 1.4.0"
  required_providers {
    aws = {
        source = "hashicorp/aws"
        version = "~> 5.23.1"
    }
    random = {
        source = "hashicorp/random"
        version = "~> 3.5.1"
    }
  }
}

resource "random_pet" "this" {
    count = var.cognito_pool_name == null ? 1 : 0
}

resource "aws_iam_saml_provider" "this" {
    for_each = var.saml_providers == null ? {} : var.saml_providers

    name = each.key
    saml_metadata_document = file(each.value.saml_metadata_document)
}

resource "aws_iam_openid_connect_provider" "this" {
    for_each = var.oidc_providers == null ? {} : var.oidc_providers

    url = each.value.url
    client_id_list = each.value.client_id_list
    thumbprint_list = each.value.thumbprint_list
}

resource "aws_cognito_identity_pool" "this" {
    identity_pool_name = var.cognito_pool_name == null ? random_pet.this[0].id : var.cognito_pool_name
    saml_provider_arns = [ for k, v in var.saml_providers : aws_iam_saml_provider.this[k].arn ]
    openid_connect_provider_arns = [ for k, v in var.oidc_providers : aws_iam_openid_connect_provider.this[k].arn ]
}