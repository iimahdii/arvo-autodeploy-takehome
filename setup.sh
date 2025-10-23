#!/bin/bash

# AutoDeploy Setup Script
# This script sets up the development environment

set -e

echo "🚀 AutoDeploy Setup Script"
echo "=========================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.9+ required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version found"

# Check Terraform
echo ""
echo "Checking Terraform..."
if ! command -v terraform &> /dev/null; then
    echo "⚠️  Terraform not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install terraform
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt update && sudo apt install terraform
    fi
else
    terraform_version=$(terraform version | head -n1 | awk '{print $2}')
    echo "✓ Terraform $terraform_version found"
fi

# Check Docker (optional)
echo ""
echo "Checking Docker (optional for container deployments)..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo "✓ Docker $docker_version found"
else
    echo "⚠️  Docker not found. Container deployments will not work."
    echo "   Install from: https://docs.docker.com/get-docker/"
fi

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your credentials:"
    echo "   - Add cloud provider credentials (AWS/GCP/Azure)"
    echo "   - Add LLM API key (OpenAI or Anthropic) - optional but recommended"
    echo ""
    echo "   Run: nano .env"
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p logs
mkdir -p deployments
mkdir -p cloned_repos
echo "✓ Directories created"

# Make main.py executable
echo ""
echo "Making main.py executable..."
chmod +x main.py
echo "✓ main.py is now executable"

# Test installation
echo ""
echo "Testing installation..."
python3 -c "import click, rich, git, yaml, toml; print('✓ All core dependencies imported successfully')"

echo ""
echo "=========================="
echo "✅ Setup Complete!"
echo "=========================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials:"
echo "   nano .env"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Test with the example repository:"
echo "   python main.py analyze https://github.com/Arvo-AI/hello_world"
echo ""
echo "4. Deploy an application:"
echo "   python main.py deploy \\"
echo "     --repo https://github.com/Arvo-AI/hello_world \\"
echo "     --description 'Deploy this Flask application on AWS'"
echo ""
echo "For more information, see README.md"
echo ""
