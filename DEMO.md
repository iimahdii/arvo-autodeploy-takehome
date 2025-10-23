# AutoDeploy Demo Guide

This guide walks through a complete demonstration of AutoDeploy's capabilities.

## Prerequisites

1. Complete setup from README.md
2. AWS credentials configured in `.env`
3. (Optional) OpenAI or Anthropic API key for enhanced NLP

## Demo 1: Repository Analysis Only

**Objective**: Analyze a repository without deploying

```bash
python main.py analyze https://github.com/Arvo-AI/hello_world
```

**Expected Output**:
```
🚀 AutoDeploy System v1.0
Automated Cloud Deployment from Natural Language

Analyzing repository: https://github.com/Arvo-AI/hello_world

┌─────────────────────────────────────────────────────────┐
│                  Repository Analysis                    │
├─────────────────────────┬───────────────────────────────┤
│ Application Type        │ flask                         │
│ Framework               │ flask                         │
│ Language                │ python                        │
│ Entry Point             │ app.py                        │
│ Start Command           │ python app.py                 │
│ Port                    │ 5000                          │
│ Requires Database       │ No                            │
│ Requires Redis          │ No                            │
│ Has Dockerfile          │ No                            │
│ Confidence Score        │ 90%                           │
└─────────────────────────┴───────────────────────────────┘

Dependencies:
  python: 2 packages
```

**What This Demonstrates**:
- Automatic framework detection (Flask)
- Language identification (Python)
- Entry point discovery (app.py)
- Port detection (5000)
- Dependency parsing (requirements.txt)
- Confidence scoring

## Demo 2: Dry Run with Natural Language

**Objective**: Parse deployment requirements without actually deploying

```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy this Flask application on AWS using a t2.micro instance in us-east-1" \
  --dry-run \
  --output-dir ./demo-output
```

**Expected Output**:

### Step 1: Repository Analysis
```
Step 1/6: Analyzing repository...
✓ Repository analyzed successfully

┌─────────────────────────────────────────────────────────┐
│                  Repository Analysis                    │
└─────────────────────────────────────────────────────────┘
```

### Step 2: Requirement Parsing
```
Step 2/6: Parsing deployment requirements...
✓ Requirements parsed successfully

┌─────────────────────────────────────────────────────────┐
│              Deployment Requirements                    │
├─────────────────────────┬───────────────────────────────┤
│ Cloud Provider          │ AWS                           │
│ Deployment Type         │ VM                            │
│ Region                  │ us-east-1                     │
│ Instance Type           │ t2.micro                      │
│ Auto Scaling            │ No                            │
│ SSL Required            │ No                            │
└─────────────────────────┴───────────────────────────────┘
```

### Step 3: Infrastructure Strategy
```
Step 3/6: Determining infrastructure strategy...
✓ Infrastructure strategy determined

┌─────────────────────────────────────────────────────────┐
│              Infrastructure Strategy                    │
├─────────────────────────┬───────────────────────────────┤
│ Deployment Strategy     │ VM                            │
│ Compute Type            │ vm                            │
│ Instance Type           │ t2.micro                      │
│ Instance Count          │ 1 (min) - 1 (max)            │
│ Estimated Cost          │ $8.50/month (estimated)       │
└─────────────────────────┴───────────────────────────────┘

Detected flask application. Using VM deployment for simplicity 
and full control.
```

**What This Demonstrates**:
- Natural language understanding
- Cloud provider extraction (AWS)
- Instance type parsing (t2.micro)
- Region identification (us-east-1)
- Deployment strategy selection (VM)
- Cost estimation ($8.50/month)

**Generated Files** (in `./demo-output/`):
- `analysis.json` - Complete analysis results
- `terraform/main.tf` - Infrastructure code
- `terraform/variables.tf` - Configuration variables
- `terraform/outputs.tf` - Deployment outputs

## Demo 3: Complex Application with Database

**Objective**: Show intelligent decision-making for complex apps

```bash
python main.py deploy \
  --repo https://github.com/example/django-blog \
  --description "Deploy this Django blog application on AWS with PostgreSQL database and auto-scaling" \
  --dry-run
```

**Expected Infrastructure Decisions**:
- Deployment Type: **Container** (ECS Fargate)
- Database: **RDS PostgreSQL** (t3.micro)
- Networking: **VPC with public/private subnets**
- Load Balancer: **Application Load Balancer**
- Auto Scaling: **Enabled** (1-3 instances)
- Estimated Cost: **~$46/month**

**What This Demonstrates**:
- Database requirement detection
- Container strategy for apps with databases
- Load balancer for auto-scaling
- Private subnet for database security
- Cost estimation with multiple services

## Demo 4: Multi-Cloud Comparison

### AWS Deployment
```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy on AWS" \
  --dry-run
```

### GCP Deployment
```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy on Google Cloud Platform" \
  --dry-run
```

### Azure Deployment
```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy on Microsoft Azure" \
  --dry-run
```

**What This Demonstrates**:
- Multi-cloud support
- Provider-specific resource naming
- Terraform abstraction across clouds

## Demo 5: Different Deployment Types

### Serverless
```bash
python main.py deploy \
  --repo https://github.com/example/api-function \
  --description "Deploy this API as a serverless function on AWS Lambda" \
  --dry-run
```

### Kubernetes
```bash
python main.py deploy \
  --repo https://github.com/example/microservices \
  --description "Deploy this microservice application on AWS EKS" \
  --dry-run
```

### Container
```bash
python main.py deploy \
  --repo https://github.com/example/dockerized-app \
  --description "Deploy this containerized application on AWS ECS Fargate" \
  --dry-run
```

**What This Demonstrates**:
- Multiple deployment strategies
- Appropriate strategy selection
- Different infrastructure patterns

## Demo 6: Natural Language Variations

All of these should work and produce similar results:

```bash
# Formal
"Deploy this Flask application on AWS using EC2 t2.micro instance"

# Casual
"Put this Flask app on AWS"

# Detailed
"I need to deploy this Flask application to AWS in the us-west-2 region 
using a small EC2 instance with auto-scaling enabled and an SSL certificate"

# Production-focused
"Production deployment of this Flask app on AWS with database, Redis, 
load balancer, and auto-scaling"
```

**What This Demonstrates**:
- Flexible natural language understanding
- Extraction of relevant details
- Smart defaults for missing information
- Context-aware decision making

## Demo 7: Local Repository

```bash
# Create a simple Flask app locally
mkdir my-flask-app
cd my-flask-app

cat > app.py << 'EOF'
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from AutoDeploy!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

cat > requirements.txt << 'EOF'
Flask==2.3.0
EOF

cd ..

# Deploy it
python main.py deploy \
  --repo ./my-flask-app \
  --description "Deploy this Flask app on AWS" \
  --dry-run
```

**What This Demonstrates**:
- Local directory support
- Minimal application detection
- Automatic Dockerfile generation

## Demo 8: Full Deployment (Requires AWS Credentials)

**⚠️ Warning**: This will create real AWS resources and incur costs

```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy this Flask application on AWS" \
  --output-dir ./deployment-output
```

**Deployment Process**:

1. **Repository Preparation**
   ```
   Cloning repository from https://github.com/Arvo-AI/hello_world...
   ✓ Repository prepared
   ```

2. **Analysis**
   ```
   Analyzing repository...
   ✓ Repository analyzed successfully
   ```

3. **Requirement Parsing**
   ```
   Parsing deployment requirements...
   ✓ Requirements parsed successfully
   ```

4. **Infrastructure Decisions**
   ```
   Determining infrastructure strategy...
   ✓ Infrastructure strategy determined
   Estimated Cost: $8.50/month
   ```

5. **Confirmation**
   ```
   Proceed with deployment? [y/N]: y
   ```

6. **Terraform Generation**
   ```
   Generating infrastructure code...
   ✓ Terraform configuration generated
   ```

7. **Infrastructure Provisioning**
   ```
   Provisioning infrastructure...
   Initializing Terraform...
   Planning infrastructure changes...
   Applying infrastructure changes (this may take several minutes)...
   ✓ Infrastructure provisioned
   ```

8. **Application Deployment**
   ```
   Deploying application...
   Building Docker image...
   Deploying to VM at 54.123.45.67...
   ✓ Application deployed
   ```

9. **Verification**
   ```
   Verifying deployment...
   ✓ Deployment verified
   ```

10. **Success**
    ```
    🎉 Deployment Successful!
    
    ┌─────────────────────────────────────────────────────┐
    │           Deployment Information                    │
    ├─────────────────────┬───────────────────────────────┤
    │ Status              │ ✓ Running                     │
    │ Type                │ vm                            │
    │ Instance IP         │ 54.123.45.67                  │
    │ Application URL     │ http://54.123.45.67:5000     │
    │ Port                │ 5000                          │
    └─────────────────────┴───────────────────────────────┘
    ```

**Generated Artifacts**:
- `deployment-output/terraform/` - Infrastructure code
- `deployment-output/deployment.json` - Deployment details
- `logs/deployment_*.log` - Detailed logs

## Demo 9: Error Handling

### Invalid Repository
```bash
python main.py deploy \
  --repo https://github.com/invalid/repo \
  --description "Deploy on AWS"
```

**Expected**: Clear error message about repository not found

### Missing Credentials
```bash
# Remove AWS credentials temporarily
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy on AWS"
```

**Expected**: Clear error about missing AWS credentials with instructions

### Ambiguous Description
```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy"
```

**Expected**: System uses smart defaults and proceeds with AWS

## Demo 10: Comparing Terraform Output

**View Generated Terraform**:
```bash
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy Flask app on AWS with PostgreSQL" \
  --dry-run \
  --output-dir ./tf-output

# View the generated Terraform
cat ./tf-output/terraform/main.tf
```

**What to Look For**:
- VPC and networking configuration
- Security group rules
- EC2 instance or ECS task definition
- RDS database configuration
- Load balancer setup (if applicable)
- Auto-scaling configuration (if applicable)

## Performance Benchmarks

**Repository Analysis**: ~2-5 seconds
**NLP Parsing (with LLM)**: ~1-3 seconds
**NLP Parsing (rule-based)**: <1 second
**Terraform Generation**: <1 second
**Terraform Apply**: 3-10 minutes (depending on resources)
**Total Deployment Time**: 5-15 minutes

## Key Features Demonstrated

✅ **Intelligent Analysis**
- Framework detection
- Dependency parsing
- Database requirement detection
- Confidence scoring

✅ **Natural Language Understanding**
- Cloud provider extraction
- Deployment type inference
- Region and instance type parsing
- Smart defaults

✅ **Infrastructure Decisions**
- Optimal deployment strategy
- Resource sizing
- Cost estimation
- Security best practices

✅ **Multi-Cloud Support**
- AWS (primary)
- GCP (beta)
- Azure (beta)

✅ **Production-Ready Output**
- Terraform infrastructure as code
- Docker containerization
- VPC networking
- Load balancing
- Auto-scaling

✅ **Developer Experience**
- Beautiful terminal output
- Detailed logging
- Clear error messages
- Progress indicators

## Troubleshooting Demo Issues

### Issue: "Terraform not found"
```bash
# Install Terraform
brew install terraform  # macOS
# or follow instructions in setup.sh
```

### Issue: "AWS credentials not configured"
```bash
# Configure AWS CLI
aws configure

# Or add to .env
echo "AWS_ACCESS_KEY_ID=your_key" >> .env
echo "AWS_SECRET_ACCESS_KEY=your_secret" >> .env
```

### Issue: "LLM API key not found"
```bash
# System will automatically fall back to rule-based parsing
# Or add API key to .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

## Next Steps

After completing these demos, you should understand:

1. How AutoDeploy analyzes repositories
2. How natural language is parsed into infrastructure requirements
3. How intelligent decisions are made about deployment strategy
4. How Terraform infrastructure is generated
5. How the complete deployment process works

For production use, consider:
- Setting up proper AWS IAM roles
- Configuring custom domains
- Enabling SSL/TLS
- Setting up monitoring and alerting
- Implementing CI/CD integration
