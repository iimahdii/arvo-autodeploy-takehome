# Quick Start Guide

Get AutoDeploy running in 5 minutes.

## Prerequisites

- Python 3.9+
- Git
- (Optional) Terraform for actual deployments
- (Optional) AWS/GCP/Azure credentials

## Installation

```bash
# Clone the repository
cd Take-Home-Arvo

# Run setup script
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

## First Command

Test that everything works:

```bash
python main.py --help
```

You should see:
```
Usage: main.py [OPTIONS] COMMAND [ARGS]...

  AutoDeploy - Automated application deployment system

Commands:
  analyze  Analyze a repository without deploying
  deploy   Deploy an application to the cloud
```

## Analyze a Repository

Try analyzing the example repository:

```bash
python main.py analyze https://github.com/Arvo-AI/hello_world
```

**Expected output**: Repository analysis showing Flask application detected

## Dry Run Deployment

Test deployment logic without actually deploying:

```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy this Flask application on AWS" \
  --dry-run
```

**Expected output**: 
- Repository analysis
- Deployment requirements parsing
- Infrastructure strategy
- Cost estimation

## Configuration (Optional)

For actual deployments, configure credentials:

```bash
# Edit .env file
nano .env

# Add your AWS credentials
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here

# (Optional) Add LLM API key for better NLP
OPENAI_API_KEY=sk-...
```

## Full Deployment (Requires AWS Credentials)

⚠️ **Warning**: This creates real AWS resources and incurs costs (~$8.50/month)

```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy this Flask application on AWS"
```

The system will:
1. Analyze the repository
2. Parse your requirements
3. Show cost estimate
4. Ask for confirmation
5. Provision infrastructure with Terraform
6. Deploy the application
7. Provide access URL

## Common Commands

### Analyze any repository
```bash
python main.py analyze <github-url>
```

### Deploy with specific requirements
```bash
python main.py deploy \
  --repo <github-url> \
  --description "Deploy on AWS with PostgreSQL database"
```

### Save analysis to file
```bash
python main.py deploy \
  --repo <github-url> \
  --description "Deploy on AWS" \
  --dry-run \
  --output-dir ./my-analysis
```

## Troubleshooting

### "Module not found" error
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Terraform not found"
```bash
# Install Terraform
brew install terraform  # macOS
# or follow: https://www.terraform.io/downloads
```

### "AWS credentials not found"
```bash
# Check credentials
aws sts get-caller-identity

# Or configure
aws configure
```

## Next Steps

- Read [README.md](README.md) for comprehensive documentation
- Check [DEMO.md](DEMO.md) for detailed examples
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- See [SOURCES.md](SOURCES.md) for dependencies

## Support

For issues or questions:
1. Check the documentation files
2. Review error messages carefully
3. Ensure all prerequisites are installed
4. Verify credentials are configured

## Example Output

When you run a dry-run deployment, you'll see:

```
🚀 AutoDeploy System v1.0

📋 Deployment Request
Repository: https://github.com/Arvo-AI/hello_world
Description: Deploy this Flask application on AWS
Mode: Dry Run (Analysis Only)

Step 1/6: Analyzing repository...
✓ Repository analyzed successfully

┌─────────────────────────────────────────────────────────┐
│                  Repository Analysis                    │
├─────────────────────────┬───────────────────────────────┤
│ Application Type        │ flask                         │
│ Framework               │ flask                         │
│ Language                │ python                        │
│ Port                    │ 5000                          │
│ Confidence Score        │ 90%                           │
└─────────────────────────┴───────────────────────────────┘

Step 2/6: Parsing deployment requirements...
✓ Requirements parsed successfully

Step 3/6: Determining infrastructure strategy...
✓ Infrastructure strategy determined

Estimated Cost: $8.50/month (estimated)

Dry run completed. No deployment performed.
```

---

**You're ready to go! 🚀**
