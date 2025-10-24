# 🚀 AutoDeploy - Automated Cloud Deployment System

**Intelligent, natural language-driven application deployment to AWS, GCP, and Azure**

AutoDeploy is a sophisticated backend system that automates the entire process of deploying applications to cloud infrastructure. Simply provide a natural language description and a GitHub repository, and AutoDeploy handles everything from code analysis to infrastructure provisioning to application deployment.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [How It Works](#how-it-works)
- [Technical Deep Dive](#technical-deep-dive)
- [Configuration](#configuration)
- [Supported Technologies](#supported-technologies)
- [Cost Estimation](#cost-estimation)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## ✨ Features

### Core Capabilities

- **🧠 Intelligent Repository Analysis**: Automatically detects application type, framework, dependencies, and deployment requirements
- **💬 Natural Language Processing**: Understands deployment requirements from plain English descriptions
- **🏗️ Smart Infrastructure Decisions**: Determines optimal deployment strategy (VM, containers, Kubernetes, serverless)
- **☁️ Multi-Cloud Support**: Deploy to AWS, GCP, or Azure with a single command
- **🔧 Infrastructure as Code**: Generates production-ready Terraform configurations
- **🐳 Automatic Containerization**: Creates optimized Dockerfiles when needed
- **📊 Comprehensive Logging**: Detailed logs of every deployment step
- **💰 Cost Estimation**: Provides monthly cost estimates before deployment

### Supported Deployment Strategies

- **Virtual Machines** (EC2, GCE, Azure VMs)
- **Containers** (ECS Fargate, Cloud Run)
- **Kubernetes** (EKS, GKE, AKS)
- **Serverless** (Lambda, Cloud Functions)

### Supported Services

- Managed databases (RDS, Cloud SQL, Azure Database)
- Redis/ElastiCache
- Load balancers
- Auto-scaling groups
- VPC networking
- SSL/TLS certificates

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Input Layer                        │
│  (Natural Language Description + GitHub Repo/Zip)          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Analysis Layer                             │
│  ┌──────────────────┐      ┌──────────────────┐           │
│  │ Repository       │      │ NLP Requirement  │           │
│  │ Analyzer         │      │ Parser           │           │
│  │ - Detect app type│      │ - Parse intent   │           │
│  │ - Find deps      │      │ - Extract cloud  │           │
│  │ - Identify DB    │      │ - Determine type │           │
│  └──────────────────┘      └──────────────────┘           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Decision Engine Layer                          │
│  ┌──────────────────────────────────────────────┐          │
│  │ Infrastructure Decision Engine               │          │
│  │ - Choose deployment strategy                 │          │
│  │ - Size compute resources                     │          │
│  │ - Configure networking                       │          │
│  │ - Select database options                    │          │
│  │ - Estimate costs                             │          │
│  └──────────────────────────────────────────────┘          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            Infrastructure Generation Layer                  │
│  ┌──────────────────────────────────────────────┐          │
│  │ Terraform Generator                          │          │
│  │ - Generate main.tf                           │          │
│  │ - Create variables.tf                        │          │
│  │ - Build outputs.tf                           │          │
│  │ - Generate user_data scripts                 │          │
│  └──────────────────────────────────────────────┘          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Deployment Orchestration Layer                 │
│  ┌──────────────────────────────────────────────┐          │
│  │ Deployment Orchestrator                      │          │
│  │ 1. Clone repository                          │          │
│  │ 2. Build application (if needed)             │          │
│  │ 3. Create Dockerfile (if needed)             │          │
│  │ 4. Apply Terraform                           │          │
│  │ 5. Deploy application                        │          │
│  │ 6. Verify deployment                         │          │
│  └──────────────────────────────────────────────┘          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Cloud Infrastructure                      │
│         (AWS / GCP / Azure Resources)                       │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Terraform 1.0+
- Docker (for containerized deployments)
- Cloud provider credentials (AWS/GCP/Azure)
- OpenAI or Anthropic API key (optional, for enhanced NLP)

### Installation

```bash
# Clone the repository
git clone https://github.com/iimahdii/arvo-autodeploy-takehome.git
cd arvo-autodeploy-takehome

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Environment Setup

Edit `.env` file with your credentials:

```bash
# LLM API Keys (optional but recommended)
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# AWS Credentials
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# For GCP 
GOOGLE_APPLICATION_CREDENTIALS=/Users/mahdi/.gcp/mahdi-mirhoseini-key.json
GCP_PROJECT_ID=mahdi-mirhoseini
GCP_PROJECT_NUMBER=64889010356
```

### First Deployment

```bash
# Deploy the example application
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy this Flask application on AWS"

# Or analyze without deploying
python main.py deploy \
  --repo https://github.com/Arvo-AI/hello_world \
  --description "Deploy this Flask application on AWS" \
  --dry-run
```

## 📚 Usage Examples

### Example 1: Simple Flask App

```bash
python main.py deploy \
  --repo https://github.com/iimahdii/flask-app \
  --description "Deploy this Flask application on AWS using a t2.micro instance"
```

### Example 2: Django with Database

```bash
python main.py deploy \
  --repo https://github.com/iimahdii/django-app \
  --description "Deploy this Django application on AWS with PostgreSQL database in us-west-2"
```

### Example 3: Node.js with Auto-Scaling

```bash
python main.py deploy \
  --repo https://github.com/iimahdii/express-api \
  --description "Deploy this Express API on GCP with auto-scaling and load balancer"
```

### Example 4: Containerized Microservice

```bash
python main.py deploy \
  --repo https://github.com/iimahdii/microservice \
  --description "Deploy this containerized application on AWS ECS Fargate with Redis"
```

### Example 5: Local Repository

```bash
python main.py deploy \
  --repo /path/to/local/project \
  --description "Deploy this application on Azure with SSL"
```

### Example 6: Dry Run Analysis

```bash
python main.py deploy \
  --repo https://github.com/iimahdii/app \
  --description "Deploy on AWS" \
  --dry-run \
  --output-dir ./analysis
```

### Example 7: Repository Analysis Only

```bash
python main.py analyze https://github.com/iimahdii/app
```

## 🔍 How It Works

### Phase 1: Repository Analysis

The **Repository Analyzer** performs deep inspection of your codebase:

1. **Language Detection**: Identifies primary programming language
2. **Framework Detection**: Recognizes Flask, Django, Express, React, etc.
3. **Dependency Parsing**: Reads `requirements.txt`, `package.json`, `Gemfile`, etc.
4. **Database Detection**: Identifies PostgreSQL, MySQL, MongoDB, Redis requirements
5. **Entry Point Discovery**: Finds `app.py`, `main.py`, `index.js`, etc.
6. **Command Inference**: Determines build and start commands
7. **Port Detection**: Extracts application port from config files
8. **Environment Variables**: Discovers required env vars from `.env.example`

**Confidence Scoring**: Each analysis receives a confidence score (0-1) based on:
- Framework detection certainty
- Entry point identification
- Dependency file presence
- Configuration completeness

### Phase 2: Natural Language Processing

The **Requirement Parser** understands deployment intent:

**With LLM (OpenAI/Anthropic)**:
- Uses GPT-4 or Claude to parse complex requirements
- Understands context and implicit requirements
- Handles ambiguous or incomplete descriptions

**Without LLM (Rule-Based Fallback)**:
- Pattern matching for cloud providers (AWS, GCP, Azure)
- Keyword extraction for deployment types
- Region and instance type detection
- Scaling and SSL requirement inference

**Extracted Information**:
- Cloud provider preference
- Deployment type (VM, container, K8s, serverless)
- Region/zone
- Instance sizing
- Scaling requirements
- Custom domain and SSL needs
- Additional services (database, Redis, load balancer)

### Phase 3: Infrastructure Decision Engine

The **Decision Engine** makes intelligent infrastructure choices:

**Compute Strategy**:
- Simple apps (Flask, Express) → VM or container
- Apps with databases → Container for isolation
- Multi-service apps → Kubernetes
- Event-driven apps → Serverless

**Resource Sizing**:
- Analyzes application complexity
- Considers database requirements
- Factors in scaling needs
- Balances cost vs. performance

**Networking**:
- VPC creation for security
- Public/private subnet configuration
- Load balancer for scaled deployments
- SSL/TLS for production apps

**Database Configuration**:
- Managed database selection (RDS, Cloud SQL)
- Instance class based on app needs
- Backup and retention policies
- Multi-AZ for high availability (optional)

**Cost Estimation**:
- Computes monthly infrastructure costs
- Includes compute, database, networking
- Provides transparency before deployment

### Phase 4: Terraform Generation

The **Terraform Generator** creates infrastructure as code:

**Generated Files**:
- `main.tf`: Core infrastructure resources
- `variables.tf`: Configurable parameters
- `outputs.tf`: Deployment information
- `user_data.sh`: VM initialization scripts

**AWS Resources Created**:
- VPC with public/private subnets
- Internet Gateway and Route Tables
- Security Groups with proper ingress/egress
- EC2 instances or ECS Fargate tasks
- RDS database instances (if needed)
- ElastiCache Redis (if needed)
- Application Load Balancer (if needed)
- Auto Scaling Groups (if enabled)

**Best Practices**:
- Least privilege security groups
- Encrypted storage
- Backup retention
- Tagging for resource management
- Modular and reusable code

### Phase 5: Deployment Orchestration

The **Orchestrator** executes the deployment:

1. **Repository Preparation**
   - Clones Git repository
   - Extracts zip files
   - Copies local directories

2. **Application Build**
   - Runs build commands (npm build, etc.)
   - Compiles TypeScript/assets
   - Generates static files

3. **Containerization**
   - Creates optimized Dockerfile if missing
   - Multi-stage builds for production
   - Minimal base images
   - Proper layer caching

4. **Infrastructure Provisioning**
   - Terraform init
   - Terraform plan (review changes)
   - Terraform apply (create resources)
   - Capture outputs (IPs, endpoints)

5. **Automatic Code Adjustments** ⭐
   - Replaces `localhost` with deployed VM's public IP
   - Converts hardcoded URLs to relative paths
   - Scans HTML, JavaScript, TypeScript files
   - **Minimal user intervention** - fully automated
   - Addresses common deployment issues automatically

6. **Application Deployment**
   - VM: SCP files, SSH commands, systemd service
   - Container: Docker build, push to registry, deploy
   - Kubernetes: Apply manifests, configure ingress
   - Serverless: Package and deploy function

6. **Verification**
   - Health check endpoints
   - Service status validation
   - Log inspection
   - Performance baseline

### Phase 6: Post-Deployment

**Outputs Provided**:
- Public IP or load balancer DNS
- Application URL
- Database endpoints
- SSH access information
- Deployment logs
- Cost breakdown

**Generated Artifacts**:
- Terraform state files
- Deployment configuration
- Access credentials
- Rollback instructions

## 🔧 Technical Deep Dive

### Repository Analyzer Implementation

**Key Classes**:
```python
class RepositoryAnalyzer:
    - _detect_language(): File extension analysis
    - _detect_framework(): Pattern matching + content inspection
    - _parse_dependencies(): Multi-format dependency parsing
    - _detect_database(): Dependency + keyword analysis
    - _find_entry_point(): Convention-based discovery
    - _calculate_confidence(): Multi-factor scoring
```

**Detection Algorithms**:
- **Framework Detection**: Weighted scoring system
  - File existence: +1 point
  - Import statements: +2 points
  - Threshold: >0 for positive match

- **Database Detection**: Two-phase approach
  1. Dependency analysis (psycopg2, mysql, etc.)
  2. Code scanning for DB keywords

- **Port Detection**: Priority order
  1. Environment files (.env)
  2. Configuration files (config.py, settings.py)
  3. Framework defaults

### NLP Requirement Parser

**LLM Integration**:
```python
class RequirementParser:
    - Supports OpenAI GPT-4 and Anthropic Claude
    - Structured output with JSON schema
    - Temperature: 0.1 for consistency
    - Fallback to rule-based parsing
```

**Prompt Engineering**:
- Clear role definition (DevOps expert)
- Structured output format (JSON)
- Context inclusion (app analysis)
- Decision rules and defaults
- Examples for few-shot learning

**Rule-Based Fallback**:
- Regex patterns for cloud providers
- Keyword matching for deployment types
- Region pattern recognition
- Smart defaults based on app type

### Infrastructure Decision Engine

**Decision Matrix**:

| App Type | Has DB | Complexity | → Strategy |
|----------|--------|------------|------------|
| Flask/Express | No | Low | VM |
| Flask/Express | Yes | Medium | Container |
| Django/Rails | Yes | Medium | Container |
| Microservices | Yes | High | Kubernetes |
| API Gateway | No | Low | Serverless |

**Cost Optimization**:
- Smallest viable instance types
- Single-AZ for development
- Spot instances (future)
- Reserved instances (future)

### Terraform Generator

**Template System**:
- Jinja2 templating for flexibility
- Conditional resource creation
- Variable parameterization
- Output extraction

**Security Hardening**:
- Minimal security group rules
- Private subnets for databases
- No hardcoded credentials
- Encrypted storage by default

### Deployment Orchestrator

**Error Handling**:
- Try-catch at each phase
- Detailed error messages
- Rollback capabilities (future)
- Comprehensive logging

**Idempotency**:
- Terraform state management
- Resource tagging
- Conditional creation

## ⚙️ Configuration

### Cloud Provider Setup

#### AWS
```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

# Option 2: AWS CLI
aws configure

# Option 3: .env file
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

#### GCP
```bash
# Create service account and download JSON key
gcloud iam service-accounts create autodeploy
gcloud iam service-accounts keys create key.json \
  --iam-account autodeploy@project.iam.gserviceaccount.com

# Set in .env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
GCP_PROJECT_ID=your-project-id
```

#### Azure
```bash
# Login and get credentials
az login
az account show

# Set in .env
AZURE_SUBSCRIPTION_ID=...
AZURE_TENANT_ID=...
```

### LLM API Keys

**OpenAI**:
```bash
# Get key from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-...
```

**Anthropic**:
```bash
# Get key from https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-...
```

## 🛠️ Supported Technologies

### Languages
- Python (3.7+)
- JavaScript/Node.js
- TypeScript
- Ruby
- PHP
- Go
- Java

### Frameworks

**Python**:
- Flask
- Django
- FastAPI
- Pyramid

**JavaScript/TypeScript**:
- Express.js
- Next.js
- React
- Vue.js
- Angular
- NestJS

**Ruby**:
- Ruby on Rails
- Sinatra

**PHP**:
- Laravel
- Symfony

**Java**:
- Spring Boot
- Micronaut

### Databases
- PostgreSQL
- MySQL
- MongoDB
- Redis
- SQLite

### Cloud Providers
- AWS (Primary support)
- GCP (Beta)
- Azure (Beta)

## 💰 Cost Estimation

### AWS Pricing Examples

**Micro Deployment** (t2.micro):
- EC2 t2.micro: $8.50/month
- RDS t3.micro: $15/month
- Data transfer: $5/month
- **Total: ~$28/month**

**Small Deployment** (t2.small):
- EC2 t2.small: $17/month
- RDS t3.small: $30/month
- Load Balancer: $16/month
- **Total: ~$63/month**

**Container Deployment** (ECS Fargate):
- Fargate (0.25 vCPU, 512MB): $15/month
- RDS t3.micro: $15/month
- ALB: $16/month
- **Total: ~$46/month**

*Prices are estimates and vary by region and usage*

## 🐛 Troubleshooting

### Common Issues

**Issue**: "Terraform init failed"
```bash
# Solution: Check Terraform installation
terraform version

# Reinstall if needed
brew install terraform  # macOS
```

**Issue**: "AWS credentials not found"
```bash
# Solution: Verify credentials
aws sts get-caller-identity

# Or check .env file
cat .env | grep AWS
```

**Issue**: "Repository analysis failed"
```bash
# Solution: Ensure repository is accessible
git clone <repo-url>  # Test manually

# Check for required files
ls -la requirements.txt package.json
```

**Issue**: "LLM parsing failed"
```bash
# Solution: System falls back to rule-based parsing
# Or add API key to .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Run with output directory
python main.py deploy \
  --repo <repo> \
  --description <desc> \
  --output-dir ./debug
```

## 🧪 Development

### Project Structure

```
Take-Home-Arvo/
├── src/
│   ├── analyzer/
│   │   └── repo_analyzer.py      # Repository analysis
│   ├── nlp/
│   │   └── requirement_parser.py  # NLP processing
│   ├── infrastructure/
│   │   ├── decision_engine.py     # Infrastructure decisions
│   │   └── terraform_generator.py # Terraform generation
│   ├── deployer/
│   │   └── orchestrator.py        # Deployment orchestration
│   └── utils/
│       ├── logger.py              # Logging utilities
│       └── validators.py          # Input validation
├── main.py                        # CLI entry point
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run tests (when implemented)
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Contributing

This is a technical assessment project, but feedback is welcome:

1. Code review comments
2. Architecture suggestions
3. Performance improvements
4. Security enhancements

## 📄 License

This project was created as a technical assessment for Arvo AI.

## 🙏 Acknowledgments

- **Arvo AI** for the challenging and open-ended problem
- **Terraform** for infrastructure as code
- **OpenAI/Anthropic** for LLM capabilities
- **Rich** library for beautiful terminal output

---

**Built with ❤️ for the Arvo AI Technical Interview**

*Demonstrating deep understanding of cloud infrastructure, deployment automation, and system design*
