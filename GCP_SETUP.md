# Google Cloud Platform Setup Guide

## Overview

This guide walks through setting up AutoDeploy to deploy applications to Google Cloud Platform (GCP).

## Your GCP Project Information

Based on your setup:
- **Project Name:** Mahdi Mirhoseini
- **Project ID:** `mahdi-mirhoseini`
- **Project Number:** `64889010356`

## Prerequisites

1. GCP Account with billing enabled
2. `gcloud` CLI installed
3. Project created (you already have this!)

## Step-by-Step Setup

### 1. Install Google Cloud SDK

```bash
# macOS
brew install google-cloud-sdk

# Or download from:
# https://cloud.google.com/sdk/docs/install

# Verify installation
gcloud --version
```

### 2. Authenticate and Set Project

```bash
# Login to GCP
gcloud auth login

# Set your project
gcloud config set project mahdi-mirhoseini

# Verify
gcloud config get-value project
# Should output: mahdi-mirhoseini
```

### 3. Enable Required APIs

```bash
# Enable Compute Engine API
gcloud services enable compute.googleapis.com

# Enable Cloud Run API (for container deployments)
gcloud services enable run.googleapis.com

# Enable Cloud SQL API (for database deployments)
gcloud services enable sqladmin.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage.googleapis.com

# Enable IAM API
gcloud services enable iam.googleapis.com

# Verify enabled services
gcloud services list --enabled
```

### 4. Create Service Account

```bash
# Create service account for AutoDeploy
gcloud iam service-accounts create autodeploy-sa \
    --display-name="AutoDeploy Service Account" \
    --description="Service account for automated deployments"

# Grant necessary permissions
gcloud projects add-iam-policy-binding mahdi-mirhoseini \
    --member="serviceAccount:autodeploy-sa@mahdi-mirhoseini.iam.gserviceaccount.com" \
    --role="roles/compute.admin"

gcloud projects add-iam-policy-binding mahdi-mirhoseini \
    --member="serviceAccount:autodeploy-sa@mahdi-mirhoseini.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding mahdi-mirhoseini \
    --member="serviceAccount:autodeploy-sa@mahdi-mirhoseini.iam.gserviceaccount.com" \
    --role="roles/cloudsql.admin"

gcloud projects add-iam-policy-binding mahdi-mirhoseini \
    --member="serviceAccount:autodeploy-sa@mahdi-mirhoseini.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# List service accounts to verify
gcloud iam service-accounts list
```

### 5. Create and Download Service Account Key

```bash
# Create key directory
mkdir -p ~/.gcp

# Generate service account key
gcloud iam service-accounts keys create ~/.gcp/mahdi-mirhoseini-key.json \
    --iam-account=autodeploy-sa@mahdi-mirhoseini.iam.gserviceaccount.com

# Verify key was created
ls -la ~/.gcp/mahdi-mirhoseini-key.json

# Set permissions (important for security)
chmod 600 ~/.gcp/mahdi-mirhoseini-key.json
```

⚠️ **Security Note:** Never commit this JSON file to Git! It's like your password.

### 6. Configure Environment Variables

Edit your `.env` file:

```bash
# Copy example if you haven't
cp .env.example .env

# Edit .env file
nano .env
```

Add these values:

```bash
# GCP Credentials
GOOGLE_APPLICATION_CREDENTIALS=/Users/mahdi/.gcp/mahdi-mirhoseini-key.json
GCP_PROJECT_ID=mahdi-mirhoseini
GCP_PROJECT_NUMBER=64889010356
GCP_REGION=us-central1

# Optional: Add OpenAI key for better NLP
OPENAI_API_KEY=sk-your-key-here
```

### 7. Verify Setup

```bash
# Test GCP authentication
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS=~/.gcp/mahdi-mirhoseini-key.json

# Test with gcloud
gcloud compute zones list --project=mahdi-mirhoseini
```

## Test Deployment to GCP

### Option 1: Analyze Only (Safe)

```bash
python main.py analyze https://github.com/Arvo-AI/hello_world
```

### Option 2: Dry Run (No actual deployment)

```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy this Flask application on Google Cloud Platform" \
  --dry-run
```

**Expected output:**
- Cloud provider detected: **GCP**
- Deployment strategy: **VM** or **Container**
- Instance type: **e2-micro** (GCP equivalent of AWS t2.micro)
- Cost estimate: **~$7-9/month**

### Option 3: Actual Deployment (⚠️ Costs Money!)

```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy this Flask application on GCP in us-central1"
```

**What happens:**
1. ✅ Analyzes repository
2. ✅ Detects Flask application
3. ✅ Generates Terraform for GCP
4. ✅ Creates VPC and networking
5. ✅ Provisions Compute Engine instance
6. ✅ Deploys application
7. ✅ Returns public IP address

## GCP Resources Created

### For Simple Flask App:

**Compute Resources:**
- ✅ VPC Network (`autodeploy-vpc`)
- ✅ Subnet (`autodeploy-subnet`)
- ✅ Firewall Rules (HTTP, SSH)
- ✅ Compute Engine Instance (e2-micro)
- ✅ External IP Address

**Estimated Cost:** ~$7-9/month

### For App with Database:

**Additional Resources:**
- ✅ Cloud SQL Instance (PostgreSQL/MySQL)
- ✅ Private VPC Peering
- ✅ Load Balancer (if scaling enabled)
- ✅ Cloud Storage Bucket (for backups)

**Estimated Cost:** ~$30-50/month

## Terraform Configuration for GCP

AutoDeploy generates Terraform like this for GCP:

```hcl
# Provider configuration
provider "google" {
  credentials = file(var.credentials_file)
  project     = var.project_id
  region      = var.region
}

# VPC Network
resource "google_compute_network" "main" {
  name                    = "autodeploy-vpc"
  auto_create_subnetworks = false
}

# Subnet
resource "google_compute_subnetwork" "main" {
  name          = "autodeploy-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.main.id
}

# Firewall rule for HTTP
resource "google_compute_firewall" "http" {
  name    = "allow-http"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["80", "5000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server"]
}

# Compute Engine Instance
resource "google_compute_instance" "app" {
  name         = "autodeploy-app"
  machine_type = "e2-micro"
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2004-lts"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.main.id
    
    access_config {
      # Ephemeral external IP
    }
  }

  metadata_startup_script = file("${path.module}/startup.sh")

  tags = ["http-server"]
}
```

## Cost Management

### Free Tier

GCP offers free tier:
- ✅ 1 e2-micro instance per month (us-central1, us-west1, us-east1)
- ✅ 30 GB standard persistent disk
- ✅ 1 GB network egress

**Your Flask app might run free!** 🎉

### View Costs

```bash
# View current costs
gcloud billing accounts list
gcloud billing projects describe mahdi-mirhoseini

# Or check Cloud Console:
# https://console.cloud.google.com/billing
```

### Set Budget Alerts

```bash
# Set up budget alert at $10
# Go to: https://console.cloud.google.com/billing/budgets

# Or use gcloud (requires additional setup)
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT \
    --display-name="AutoDeploy Budget" \
    --budget-amount=10
```

## Cleanup / Destroy Resources

### Using Terraform

```bash
# Navigate to deployment output directory
cd deployments/[deployment-id]/terraform

# Destroy all resources
terraform destroy -auto-approve
```

### Using gcloud

```bash
# Delete specific instance
gcloud compute instances delete autodeploy-app \
    --zone=us-central1-a \
    --project=mahdi-mirhoseini

# Delete VPC
gcloud compute networks delete autodeploy-vpc \
    --project=mahdi-mirhoseini

# Delete all resources (careful!)
gcloud compute instances list --project=mahdi-mirhoseini
# Delete each one
```

## Troubleshooting

### Issue: "Permission denied"

```bash
# Check service account has correct roles
gcloud projects get-iam-policy mahdi-mirhoseini \
    --flatten="bindings[].members" \
    --filter="bindings.members:autodeploy-sa@mahdi-mirhoseini.iam.gserviceaccount.com"

# Grant missing role
gcloud projects add-iam-policy-binding mahdi-mirhoseini \
    --member="serviceAccount:autodeploy-sa@mahdi-mirhoseini.iam.gserviceaccount.com" \
    --role="roles/ROLE_NAME"
```

### Issue: "API not enabled"

```bash
# Enable all required APIs
gcloud services enable compute.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com \
    --project=mahdi-mirhoseini
```

### Issue: "Quota exceeded"

```bash
# Check quotas
gcloud compute project-info describe --project=mahdi-mirhoseini

# Request quota increase:
# https://console.cloud.google.com/iam-admin/quotas
```

### Issue: "Credentials not found"

```bash
# Verify credentials file exists
ls -la ~/.gcp/mahdi-mirhoseini-key.json

# Verify environment variable
echo $GOOGLE_APPLICATION_CREDENTIALS

# Re-export if needed
export GOOGLE_APPLICATION_CREDENTIALS=/Users/mahdi/.gcp/mahdi-mirhoseini-key.json
```

## Security Best Practices for GCP

### 1. Service Account Permissions

```bash
# Follow principle of least privilege
# Only grant necessary roles

# View all roles
gcloud iam roles list --project=mahdi-mirhoseini

# View what a role can do
gcloud iam roles describe roles/compute.admin
```

### 2. Key Rotation

```bash
# List keys
gcloud iam service-accounts keys list \
    --iam-account=autodeploy-sa@mahdi-mirhoseini.iam.gserviceaccount.com

# Create new key
gcloud iam service-accounts keys create ~/.gcp/new-key.json \
    --iam-account=autodeploy-sa@mahdi-mirhoseini.iam.gserviceaccount.com

# Delete old key
gcloud iam service-accounts keys delete KEY_ID \
    --iam-account=autodeploy-sa@mahdi-mirhoseini.iam.gserviceaccount.com
```

### 3. VPC Security

- ✅ Use private subnets for databases
- ✅ Minimal firewall rules
- ✅ Enable VPC Flow Logs
- ✅ Use Cloud NAT for private instances

### 4. Monitoring

```bash
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# View logs
gcloud logging read "resource.type=gce_instance" \
    --project=mahdi-mirhoseini \
    --limit=50
```

## Next Steps

1. ✅ Complete setup above
2. ✅ Test with dry-run
3. ✅ Deploy test application
4. ✅ Verify it works
5. ✅ Destroy resources to avoid costs
6. ✅ Ready for production deployments!

## Resources

- [GCP Console](https://console.cloud.google.com/)
- [GCP Documentation](https://cloud.google.com/docs)
- [GCP Pricing Calculator](https://cloud.google.com/products/calculator)
- [GCP Free Tier](https://cloud.google.com/free)
- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)

## Your Project Links

- **Console:** https://console.cloud.google.com/home/dashboard?project=mahdi-mirhoseini
- **Compute Engine:** https://console.cloud.google.com/compute/instances?project=mahdi-mirhoseini
- **Cloud Run:** https://console.cloud.google.com/run?project=mahdi-mirhoseini
- **Billing:** https://console.cloud.google.com/billing?project=mahdi-mirhoseini
- **IAM:** https://console.cloud.google.com/iam-admin/iam?project=mahdi-mirhoseini

---

**Ready to deploy to Google Cloud! 🚀**
