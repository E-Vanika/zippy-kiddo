variable "tenancy_ocid" {
  description = "OCI tenancy OCID"
  type        = string
  sensitive   = true
}

variable "user_ocid" {
  description = "OCI user OCID"
  type        = string
  sensitive   = true
}

variable "fingerprint" {
  description = "OCI API key fingerprint"
  type        = string
  sensitive   = true
}

variable "private_key_path" {
  description = "OCI API private key path"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "OCI region"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key"
  type        = string
  sensitive   = true
}

variable "fault_domain" {
  description = "OCI fault domain. Empty means OCI chooses."
  type        = string
  default     = null
}

variable "instance_shape" {
  description = "Always Free OCI compute shape"
  type        = string

  validation {
    condition = contains(
      [
        "VM.Standard.A1.Flex",
        "VM.Standard.E2.1.Micro"
      ],
      var.instance_shape
    )

    error_message = "Only OCI Always Free compute shapes are allowed."
  }
}

variable "instance_name" {
  description = "OCI VM name"
  type        = string
  default     = "free-terraform-vm"
}