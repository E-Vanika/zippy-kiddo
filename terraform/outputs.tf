output "instance_name" {
  description = "VM name"
  value       = oci_core_instance.free_vm.display_name
}

output "instance_id" {
  description = "OCI instance OCID"
  value       = oci_core_instance.free_vm.id
}

output "private_ip" {
  description = "Private IP address"
  value       = oci_core_instance.free_vm.private_ip
}

output "public_ip" {
  description = "Public IP address"
  value       = oci_core_instance.free_vm.public_ip
}

output "ssh_command" {
  description = "SSH command"
  value       = "ssh ubuntu@${oci_core_instance.free_vm.public_ip}"
}