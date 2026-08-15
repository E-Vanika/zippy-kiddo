output "instance_name" {
  value = oci_core_instance.free_vm.display_name
}

output "instance_id" {
  value = oci_core_instance.free_vm.id
}

output "public_ip" {
  value = oci_core_instance.free_vm.public_ip
}

output "private_ip" {
  value = oci_core_instance.free_vm.private_ip
}

output "shape" {
  value = oci_core_instance.free_vm.shape
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/id_ed25519 ubuntu@${oci_core_instance.free_vm.public_ip}"
}