# Credential setup

Never paste a token, private key, or password into an issue, commit, chat, or
workflow file. Add credentials at:

`GitHub repository > Settings > Secrets and variables > Actions > Secrets > New repository secret`

The name must match exactly, including capital letters and underscores.

## 1. OCI credentials required by the infrastructure workflow

Create these seven **repository secrets**:

| Secret name | Value |
| --- | --- |
| `OCI_TENANCY_OCID` | The tenancy OCID beginning with `ocid1.tenancy` |
| `OCI_USER_OCID` | The user OCID beginning with `ocid1.user` |
| `OCI_FINGERPRINT` | Fingerprint shown for the OCI API signing key |
| `OCI_PRIVATE_KEY` | Entire downloaded API private-key PEM, including BEGIN and END lines |
| `OCI_REGION` | Region identifier such as `ap-hyderabad-1` |
| `SSH_PUBLIC_KEY` | Entire **public** SSH key line, normally beginning `ssh-ed25519` |
| `VM_SSH_KEY` | Entire private SSH key matching `SSH_PUBLIC_KEY`; required by bootstrap and CD |

### Generate the OCI API signing key

1. Sign in to the OCI Console.
2. Open the profile menu and select your username/User settings.
3. Open **API keys** (sometimes displayed under **Tokens and keys**).
4. Select **Add API key**.
5. Select **Generate API key pair** and download the private key.
6. Select **Add**.
7. Copy the values from the configuration preview:
   - `tenancy` becomes `OCI_TENANCY_OCID`.
   - `user` becomes `OCI_USER_OCID`.
   - `fingerprint` becomes `OCI_FINGERPRINT`.
   - `region` becomes `OCI_REGION`.
8. Open the downloaded `.pem` file in a text editor. Copy its complete contents
   into `OCI_PRIVATE_KEY`. Preserve all line breaks.
9. Store the downloaded file safely outside this repository. Never use the OCI
   API private key as the VM SSH key; they are different credentials.

### Generate the VM SSH key

In PowerShell, create a dedicated key only if you do not already have the key
whose public half is installed on the current VM:

```powershell
ssh-keygen -t ed25519 -C "zippy-kiddo" -f "$env:USERPROFILE\.ssh\zippy_kiddo"
```

1. Keep `zippy_kiddo` private and local.
2. Open `zippy_kiddo.pub` and copy the complete one-line value.
3. Add that value as the GitHub secret `SSH_PUBLIC_KEY`.
4. Open the private `zippy_kiddo` file and add its complete contents as the
   GitHub secret `VM_SSH_KEY`.
5. Do **not** put the private key into `SSH_PUBLIC_KEY` or the public key into
   `VM_SSH_KEY`.

Changing `SSH_PUBLIC_KEY` updates Terraform metadata but does not reliably
replace access on an already-created VM. Keep the private key that corresponds
to the public key already used to create the E2 instance.

## 2. Hugging Face token for the future model publishing workflow

This is optional today. The deterministic application works without it.

1. Create or sign in to a Hugging Face account.
2. Open **Settings > Access Tokens**.
3. Select **New token**.
4. Choose a **fine-grained** token.
5. Grant write access only to the Zippy Kiddo model repository. If that
   repository does not exist yet, create a public model repository first.
6. Create the token and copy it once.
7. Add it to GitHub as repository secret `HF_TOKEN`.
8. Under GitHub **Actions > Variables**, add a non-secret repository variable
   named `HF_MODEL_REPO`, with a value such as `E-Vanika/zippy-kiddo-ranker`.

Do not create a Hugging Face Inference Endpoint: it can incur cost. The intended
design downloads a small public model artifact and runs inference locally.

## 3. Kaggle token for free training notebooks

This is optional today and is normally needed only outside a Kaggle notebook.

1. Create or sign in to a Kaggle account.
2. Open `https://www.kaggle.com/settings/api`.
3. Under API tokens, select **Generate New Token**.
4. Copy the generated token.
5. Add it to GitHub as repository secret `KAGGLE_API_TOKEN`.

Kaggle notebooks authenticate natively, so do not copy this secret into a
notebook cell or commit a downloaded token file.

## 4. YouTube Data API key for optional idea discovery

This is optional and must be used only to discover candidate public videos for
manual review. Do not scrape comments, profiles, children’s data, or copyrighted
video transcripts into the training dataset.

1. Open Google Cloud Console and create a project such as `zippy-kiddo-research`.
2. Open **APIs & Services > Library**.
3. Find and enable **YouTube Data API v3**.
4. Open **APIs & Services > Credentials**.
5. Select **Create credentials > API key**.
6. Edit the key immediately.
7. Under **API restrictions**, restrict it to **YouTube Data API v3**.
8. If calls will come from a stable server IP, also add an IP application
   restriction. Until then, keep the key server-side and enforce a small quota.
9. Add the value to GitHub as repository secret `YOUTUBE_API_KEY`.

Google Cloud may request billing-account setup depending on the account or
service configuration. Because this project has a strict zero-cost rule, stop
instead of enabling billing or accepting any paid upgrade.

## 5. Secrets you do not need

- Do not create a GitHub personal access token. Actions automatically supplies
  `GITHUB_TOKEN`, and the workflows use only read permissions.
- Do not add Facebook or Instagram tokens. They are not part of the approved
  data pipeline.
- `GEMINI_API_KEY` is not used by the current application or deployment. If it
  already exists, leave it unused until a separately reviewed, free-tier model
  experiment needs it; never inject it into the web-service container.
- Do not add an OpenAI, Anthropic, or paid inference API key.
- Do not put any credential in `.env.example`, Terraform files, or `plan.md`.

## 6. Verify the setup

1. Open **Actions > OCI Terraform Infra Pipeline**.
2. Select **Run workflow** on `main`.
3. Confirm that formatting, validation, Trivy, Gitleaks, and E2 deployment pass.
4. An A1 `Out of host capacity` warning is expected and is not a failure; the E2
   Always Free VM remains deployed.
5. Open **Actions > Application CI** and run it.
6. Confirm that both the `test` and `container` jobs are green.
7. A successful push CI automatically triggers **Application CD**. CD runs the
   idempotent Ansible bootstrap, deploys the exact tested commit, checks
   readiness, and rolls back if the check fails.
8. **Bootstrap E2 VM** remains available as a manual recovery workflow; normal
   deployments do not require you to run it separately or install anything on
   your laptop.

GitHub hides secret values after creation, so keep an offline record of which
account owns each credential and its rotation date—never the values in this
repository.
