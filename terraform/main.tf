data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

data "oci_core_images" "ubuntu" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "24.04"
  shape                    = "VM.Standard.A1.Flex"

  sort_by    = "TIMECREATED"
  sort_order = "DESC"
}

resource "oci_core_vcn" "free_vcn" {
  compartment_id = var.tenancy_ocid

  display_name = "free-terraform-vcn"
  cidr_blocks  = ["10.0.0.0/16"]

  dns_label = "freevcn"
}

resource "oci_core_internet_gateway" "free_igw" {
  compartment_id = var.tenancy_ocid
  vcn_id         = oci_core_vcn.free_vcn.id

  display_name = "free-terraform-igw"
  enabled      = true
}

resource "oci_core_route_table" "free_route_table" {
  compartment_id = var.tenancy_ocid
  vcn_id         = oci_core_vcn.free_vcn.id

  display_name = "free-terraform-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.free_igw.id
  }
}

resource "oci_core_security_list" "free_security_list" {
  compartment_id = var.tenancy_ocid
  vcn_id         = oci_core_vcn.free_vcn.id

  display_name = "free-terraform-security-list"

  # SSH - ONLY YOUR CURRENT PUBLIC IP
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"

    tcp_options {
      min = 22
      max = 22
    }
  }

  # HTTP
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"

    tcp_options {
      min = 80
      max = 80
    }
  }

  # HTTPS
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"

    tcp_options {
      min = 443
      max = 443
    }
  }

  # Outbound traffic
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

resource "oci_core_subnet" "free_subnet" {
  compartment_id = var.tenancy_ocid
  vcn_id         = oci_core_vcn.free_vcn.id

  display_name = "free-terraform-public-subnet"

  cidr_block = "10.0.1.0/24"

  route_table_id    = oci_core_route_table.free_route_table.id
  security_list_ids = [oci_core_security_list.free_security_list.id]

  dns_label = "public"
}

# Automatically fetches the correct AD string for your region
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

variable "fault_domain" {
  type    = string
  default = "FAULT-DOMAIN-1"
}

resource "oci_core_instance" "free_vm" {
  # Dynamically selects the first AD in Hyderabad without needing GitHub variables
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  compartment_id      = var.tenancy_ocid
  shape               = "VM.Standard.A1.Flex" 
  fault_domain        = var.fault_domain


  shape_config {
    ocpus         = 1
    memory_in_gbs = 6
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.free_subnet.id
    assign_public_ip = true

    hostname_label = "freevm"
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu.images[0].id

    boot_volume_size_in_gbs = 50
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
  }

  freeform_tags = {
    CreatedBy = "Terraform-GitHub-Actions"
    FreeTier  = "AlwaysFree"
  }
}