terraform {
  backend "oci" {
    bucket    = "bucket-my-terrafrom-statefile-zippy-kiddo"
    namespace = "axwj7qxpzppm"
    key       = "oci-free-vm/terraform.tfstate"
    region="ap-hyderabad-1"
  }
}