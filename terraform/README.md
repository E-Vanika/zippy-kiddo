# Zippy Kiddo OCI infrastructure

Terraform runs through `.github/workflows/infra-pipeline.yaml`. The repository
does not use or require a `terraform.tfvars` file.

## GitHub configuration

Create a GitHub Environment named `production` and define these environment
secrets:

- `OCI_TENANCY_OCID`
- `OCI_USER_OCID`
- `OCI_FINGERPRINT`
- `OCI_PRIVATE_KEY`
- `OCI_REGION`
- `SSH_PUBLIC_KEY`

The workflow writes the OCI private key to the temporary GitHub runner
directory, supplies Terraform variables through `TF_VAR_*`, and deletes the
temporary key in its final cleanup step.

## Deployment order

The workflow uses one OCI remote state but applies the infrastructure in two
stages:

1. Target and apply `oci_core_instance.e2_micro_vm` with its network
   dependencies. This establishes the E2 Micro fallback without waiting for A1
   capacity.
2. Produce and apply a complete plan. This retries the A1 Flex instance. The
   specific OCI `Out of host capacity` response becomes a workflow warning, and
   the previously applied E2 VM remains available and recorded in remote state.
   Authentication, configuration, quota, and other unexpected failures still
   fail the workflow.

The plan safety checks reject any compute shape other than:

- `VM.Standard.E2.1.Micro`
- `VM.Standard.A1.Flex`

## Cost boundary

Both definitions use shapes from Oracle's Always Free program and 50 GB boot
volumes. Before the first workflow run, confirm in the OCI Console that the
shapes are marked **Always Free-eligible** in the tenancy's home region and
that enough compute and block-volume quota remains. Include the existing
`solo-sre-project` VM and any other volumes in that calculation.

Terraform cannot guarantee account-specific free-tier eligibility or prevent
charges if the OCI account has been upgraded. Do not approve a plan containing
unexpected resources.

## Network exposure

The OCI security list permits only:

- SSH from `allowed_ssh_cidr`;
- HTTP on port 80 for certificate issuance and redirect;
- HTTPS on port 443 for the application;
- ICMP inside the VCN.

Application and model ports must remain private behind the edge proxy. Outbound
traffic is enabled for security updates, image pulls, and model downloads.
