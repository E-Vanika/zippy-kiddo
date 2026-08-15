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
  description = "Path to OCI API private key"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "OCI home region"
  type        = string
}

variable "availability_domain" {
  description = "Optional OCI availability domain override for VM placement; if unset, the first AD in the tenancy is used"
  type        = string
  default     = null
}

variable "ssh_public_key" {
  description = "SSH public key for the VM"
  type        = string
  sensitive   = true
}

variable "instance_name" {
  description = "OCI VM name"
  type        = string
  default     = "free-terraform-vm"
}