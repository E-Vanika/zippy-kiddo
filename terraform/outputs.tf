output "instance_id" {
  description = "A1 instance OCID"
  value       = oci_core_instance.free_vm.id
}

output "instance_name" {
  description = "A1 instance name"
  value       = oci_core_instance.free_vm.display_name
}

output "private_ip" {
  description = "A1 private IP address"
  value       = oci_core_instance.free_vm.private_ip
}

output "public_ip" {
  description = "A1 public IP address"
  value       = oci_core_instance.free_vm.public_ip
}

output "shape" {
  description = "A1 compute shape"
  value       = oci_core_instance.free_vm.shape
}

output "ssh_command" {
  description = "A1 SSH command"
  value = format(
    "ssh -i ~/.ssh/id_ed25519 ubuntu@%s",
    oci_core_instance.free_vm.public_ip
  )
}

output "e2_micro_instance_id" {
  description = "E2 Micro instance OCID"
  value       = oci_core_instance.e2_micro_vm.id
}

output "e2_micro_private_ip" {
  description = "E2 Micro private IP address"
  value       = oci_core_instance.e2_micro_vm.private_ip
}

output "e2_micro_public_ip" {
  description = "E2 Micro public IP address"
  value       = oci_core_instance.e2_micro_vm.public_ip
}

output "e2_micro_ssh_command" {
  description = "E2 Micro SSH command"
  value = format(
    "ssh -i ~/.ssh/id_ed25519 ubuntu@%s",
    oci_core_instance.e2_micro_vm.public_ip
  )
}
