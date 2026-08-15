terraform {
  required_version = ">= 1.13.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 7.32"
    }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# ============================================================
# AVAILABILITY DOMAINS
# ============================================================

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# ============================================================
# UBUNTU ARM64 IMAGE FOR A1
# ============================================================

data "oci_core_images" "ubuntu_a1" {
  compartment_id = var.tenancy_ocid

  operating_system         = "Canonical Ubuntu"
  operating_system_version = "24.04"

  shape = "VM.Standard.A1.Flex"

  sort_by    = "TIMECREATED"
  sort_order = "DESC"
}

# ============================================================
# VCN
# ============================================================

resource "oci_core_vcn" "free_vcn" {
  compartment_id = var.tenancy_ocid

  display_name = "free-terraform-vcn"

  cidr_blocks = [
    "10.0.0.0/16"
  ]

  dns_label = "freevcn"

  freeform_tags = {
    ManagedBy = "Terraform"
    Workload  = "DevOps-Lab"
    Tier      = "Always-Free"
  }
}

# ============================================================
# INTERNET GATEWAY
# ============================================================

resource "oci_core_internet_gateway" "free_igw" {
  compartment_id = var.tenancy_ocid

  vcn_id = oci_core_vcn.free_vcn.id

  display_name = "free-terraform-igw"

  enabled = true

  freeform_tags = {
    ManagedBy = "Terraform"
  }
}

# ============================================================
# ROUTE TABLE
# ============================================================

resource "oci_core_route_table" "free_route_table" {
  compartment_id = var.tenancy_ocid

  vcn_id = oci_core_vcn.free_vcn.id

  display_name = "free-terraform-route-table"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.free_igw.id
  }

  freeform_tags = {
    ManagedBy = "Terraform"
  }
}

# ============================================================
# SECURITY LIST
# ============================================================

resource "oci_core_security_list" "free_security_list" {
  compartment_id = var.tenancy_ocid

  vcn_id = oci_core_vcn.free_vcn.id

  display_name = "free-terraform-security-list"

  # ----------------------------------------------------------
  # SSH - ONLY FROM YOUR CURRENT PUBLIC IP
  # ----------------------------------------------------------

  ingress_security_rules {
    protocol = "6"

    source = "${var.allowed_ssh_cidr}/32"

    tcp_options {
      min = 22
      max = 22
    }

    description = "SSH from administrator public IP"
  }

  # ----------------------------------------------------------
  # ICMP
  # ----------------------------------------------------------

  ingress_security_rules {
    protocol = "1"

    source = var.vcn_cidr

    description = "ICMP inside VCN"
  }

  # ----------------------------------------------------------
  # ALL OUTBOUND
  # ----------------------------------------------------------

  egress_security_rules {
    protocol = "all"

    destination = "0.0.0.0/0"

    description = "Allow outbound internet traffic"
  }

  freeform_tags = {
    ManagedBy = "Terraform"
  }
}

# ============================================================
# SUBNET
# ============================================================

resource "oci_core_subnet" "free_subnet" {
  compartment_id = var.tenancy_ocid

  vcn_id = oci_core_vcn.free_vcn.id

  display_name = "free-terraform-subnet"

  cidr_block = "10.0.1.0/24"

  route_table_id = oci_core_route_table.free_route_table.id

  security_list_ids = [
    oci_core_security_list.free_security_list.id
  ]

  dns_label = "freesubnet"

  prohibit_public_ip_on_vnic = false

  freeform_tags = {
    ManagedBy = "Terraform"
  }
}

# ============================================================
# ALWAYS FREE A1 FLEX VM
# ============================================================

resource "oci_core_instance" "free_vm" {
  compartment_id = var.tenancy_ocid

  display_name = "free-terraform-vm"

  availability_domain = (
    data.oci_identity_availability_domains.ads.availability_domains[0].name
  )

  # ==========================================================
  # A1 ONLY
  # ==========================================================

  shape = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 1
    memory_in_gbs = 6
  }

  # ==========================================================
  # VNIC
  # ==========================================================

  create_vnic_details {
    subnet_id = oci_core_subnet.free_subnet.id

    assign_public_ip = true

    hostname_label = "freevm"
  }

  # ==========================================================
  # UBUNTU ARM64
  # ==========================================================

  source_details {
    source_type = "image"

    source_id = data.oci_core_images.ubuntu_a1.images[0].id

    boot_volume_size_in_gbs = 50
  }

  # ==========================================================
  # SSH KEY
  # ==========================================================

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
  }

  # ==========================================================
  # TAGS
  # ==========================================================

  freeform_tags = {
    ManagedBy = "Terraform"
    Workload  = "DevOps-Kubernetes-Lab"
    Shape     = "VM.Standard.A1.Flex"
    Tier      = "Always-Free"
  }
}