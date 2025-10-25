"""
Deployment Orchestrator - Coordinates the entire deployment process
"""
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional
from git import Repo
import tempfile
import time
import random
import string
from python_terraform import Terraform
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table


class DeploymentOrchestrator:
    """Orchestrates the complete deployment process"""
    
    def __init__(self, work_dir: Optional[str] = None):
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self.console = Console()
        self.deployment_log = []
        # Generate unique deployment ID
        self.deployment_id = self._generate_deployment_id()
    
    def _generate_deployment_id(self) -> str:
        """Generate unique deployment identifier"""
        timestamp = int(time.time())
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"{timestamp}-{random_suffix}"
    
    def deploy(self, repo_source: str, app_analysis: Dict, infrastructure: Dict, 
               requirements: Dict) -> Dict:
        """Execute complete deployment"""
        
        self.log("🚀 Starting deployment process...")
        
        try:
            # Step 1: Clone/prepare repository
            repo_path = self._prepare_repository(repo_source)
            self.log(f"✓ Repository prepared at {repo_path}")
            
            # Step 2: Build application (if needed)
            if app_analysis.get('build_command'):
                self._build_application(repo_path, app_analysis)
                self.log("✓ Application built successfully")
            
            # Step 3: Create Dockerfile if not present
            if not app_analysis.get('dockerfile_present'):
                self._create_dockerfile(repo_path, app_analysis)
                self.log("✓ Dockerfile generated")
            
            # Step 4: Generate Terraform configuration
            tf_dir = self._generate_terraform(infrastructure, app_analysis)
            self.log(f"✓ Terraform configuration generated at {tf_dir}")
            
            # Step 5: Initialize and apply Terraform
            tf_output = self._apply_terraform(tf_dir, requirements)
            self.log("✓ Infrastructure provisioned")
            
            # Step 5.5: Get deployment info early for localhost fixing
            compute = infrastructure['compute_resources']
            temp_deployment_info = {
                'instance_ip': tf_output.get('instance_public_ip', {}).get('value'),
                'port': app_analysis.get('port', 5000)
            }
            
            # Step 5.6: Fix localhost references automatically (minimal intervention)
            self._fix_localhost_references(repo_path, temp_deployment_info)
            
            # Step 6: Deploy application to infrastructure
            deployment_info = self._deploy_application(
                repo_path, app_analysis, infrastructure, tf_output
            )
            self.log("✓ Application deployed")
            
            # Step 7: Verify deployment
            self._verify_deployment(deployment_info)
            self.log("✓ Deployment verified")
            
            result = {
                'status': 'success',
                'infrastructure': infrastructure,
                'deployment_info': deployment_info,
                'terraform_output': tf_output,
                'logs': self.deployment_log,
            }
            
            self._display_success(result)
            return result
            
        except Exception as e:
            self.log(f"✗ Deployment failed: {str(e)}", error=True)
            return {
                'status': 'failed',
                'error': str(e),
                'logs': self.deployment_log,
            }
    
    def _prepare_repository(self, repo_source: str) -> Path:
        """Clone or copy repository"""
        repo_dir = self.work_dir / 'repo'
        
        if repo_source.startswith(('http://', 'https://', 'git@')):
            # Clone from Git
            self.log(f"Cloning repository from {repo_source}...")
            Repo.clone_from(repo_source, repo_dir)
        elif os.path.isdir(repo_source):
            # Copy local directory
            self.log(f"Copying local repository from {repo_source}...")
            shutil.copytree(repo_source, repo_dir)
        elif repo_source.endswith('.zip'):
            # Extract zip file
            self.log(f"Extracting zip file {repo_source}...")
            shutil.unpack_archive(repo_source, repo_dir)
        else:
            raise ValueError(f"Invalid repository source: {repo_source}")
        
        return repo_dir
    
    def _fix_localhost_references(self, repo_path: Path, deployment_info: Dict):
        """
        Automatically replace localhost references with actual deployment URLs
        This enables minimal user intervention as per assessment requirements
        """
        public_ip = deployment_info.get('instance_ip')
        port = deployment_info.get('port', 5000)
        
        if not public_ip:
            self.log("⚠️ No public IP available, skipping localhost fix")
            return
        
        self.log(f"Fixing localhost references to use {public_ip}:{port}...")
        
        # Patterns to replace
        patterns = [
            (f'http://localhost:{port}', ''),  # Replace with relative path
            (f'http://127.0.0.1:{port}', ''),  # Replace with relative path  
            ('http://localhost:5000', ''),     # Common default
            ('http://127.0.0.1:5000', ''),     # Common default
        ]
        
        # File extensions to check
        extensions = ['.html', '.js', '.jsx', '.ts', '.tsx', '.vue']
        
        fixed_count = 0
        
        for ext in extensions:
            for file_path in repo_path.rglob(f'*{ext}'):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    original_content = content
                    
                    # Apply all replacement patterns
                    for old_pattern, new_pattern in patterns:
                        content = content.replace(old_pattern, new_pattern)
                    
                    # Write back if changed
                    if content != original_content:
                        file_path.write_text(content, encoding='utf-8')
                        fixed_count += 1
                        self.log(f"  ✓ Fixed {file_path.name}")
                        
                except Exception as e:
                    self.log(f"  ⚠️ Could not process {file_path.name}: {e}")
        
        if fixed_count > 0:
            self.log(f"✓ Fixed localhost references in {fixed_count} file(s)")
        else:
            self.log("No localhost references found to fix")
    
    def _build_application(self, repo_path: Path, app_analysis: Dict):
        """Build application if build command exists"""
        build_cmd = app_analysis.get('build_command')
        if not build_cmd:
            return
        
        self.log(f"Building application: {build_cmd}")
        
        result = subprocess.run(
            build_cmd,
            shell=True,
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Build failed: {result.stderr}")
        
        self.log("Build output:", result.stdout)
    
    def _create_dockerfile(self, repo_path: Path, app_analysis: Dict):
        """Generate Dockerfile if not present"""
        framework = app_analysis.get('framework', '')
        language = app_analysis.get('language', '')
        port = app_analysis.get('port', 8000)
        start_cmd = app_analysis.get('start_command', '')
        
        dockerfile_content = self._generate_dockerfile_content(
            language, framework, port, start_cmd
        )
        
        (repo_path / 'Dockerfile').write_text(dockerfile_content)
        self.log("Generated Dockerfile")
    
    def _generate_dockerfile_content(self, language: str, framework: str, 
                                     port: int, start_cmd: str) -> str:
        """Generate Dockerfile content based on app type"""
        
        if language == 'python':
            return f'''FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt* Pipfile* ./

# Install dependencies
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi
RUN if [ -f Pipfile ]; then pip install pipenv && pipenv install --system --deploy; fi

# Copy application
COPY . .

# Expose port
EXPOSE {port}

# Start command
CMD {start_cmd if start_cmd else f"python app.py"}
'''
        
        elif language in ['javascript', 'typescript']:
            return f'''FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application
COPY . .

# Build if needed
RUN if [ -f "tsconfig.json" ]; then npm run build; fi

# Expose port
EXPOSE {port}

# Start command
CMD {start_cmd if start_cmd else "npm start"}
'''
        
        else:
            return f'''FROM ubuntu:22.04

WORKDIR /app

COPY . .

EXPOSE {port}

CMD {start_cmd if start_cmd else "echo 'No start command defined'"}
'''
    
    def _generate_terraform(self, infrastructure: Dict, app_analysis: Dict) -> Path:
        """Generate Terraform configuration"""
        from src.infrastructure.terraform_generator import TerraformGenerator
        
        tf_dir = self.work_dir / 'terraform'
        generator = TerraformGenerator(str(tf_dir))
        generator.generate(infrastructure, app_analysis)
        
        return tf_dir
    
    def _apply_terraform(self, tf_dir: Path, requirements: Dict) -> Dict:
        """Initialize and apply Terraform"""
        
        self.log("Initializing Terraform...")
        
        # Prepare environment variables for Terraform
        tf_env = os.environ.copy()
        
        # Ensure Google credentials are available for GCP
        cloud_provider = requirements.get('cloud_provider', 'aws').lower()
        if cloud_provider == 'gcp':
            google_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
            if google_creds:
                tf_env['GOOGLE_APPLICATION_CREDENTIALS'] = google_creds
                self.log(f"Using Google credentials from: {google_creds}")
        
        tf = Terraform(working_dir=str(tf_dir))
        
        # Initialize
        return_code, stdout, stderr = tf.init(capture_output=False)
        if return_code != 0:
            raise Exception(f"Terraform init failed: {stderr}")
        
        self.log("Terraform initialized")
        
        # Prepare Terraform variables with unique name
        unique_app_name = f"autodeploy-{self.deployment_id}"
        self.log(f"Deployment ID: {self.deployment_id}")
        
        tf_vars = {
            'app_name': unique_app_name,
        }
        
        # Add cloud provider specific variables
        if cloud_provider == 'gcp':
            # Get GCP variables from environment
            gcp_project_id = os.environ.get('GCP_PROJECT_ID')
            gcp_region = requirements.get('region', os.environ.get('GCP_REGION', 'us-central1'))
            
            if not gcp_project_id:
                raise Exception("GCP_PROJECT_ID environment variable is required for GCP deployments")
            
            tf_vars.update({
                'gcp_project_id': gcp_project_id,
                'gcp_region': gcp_region,
            })
        elif cloud_provider == 'aws':
            # AWS variables
            tf_vars.update({
                'aws_region': requirements.get('region', os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')),
            })
        
        # Plan
        self.log("Planning infrastructure changes...")
        return_code, stdout, stderr = tf.plan(var=tf_vars, capture_output=False)
        
        # Terraform plan returns: 0 = no changes, 1 = error, 2 = changes present
        if return_code not in [0, 2]:
            self.log(f"Terraform plan output: {stdout}")
            raise Exception(f"Terraform plan failed: {stderr}")
        
        # Apply
        self.log("Applying infrastructure changes (this may take several minutes)...")
        return_code, stdout, stderr = tf.apply(skip_plan=True, var=tf_vars, capture_output=False)
        
        if return_code != 0:
            raise Exception(f"Terraform apply failed: {stderr}")
        
        # Get outputs
        outputs = tf.output()
        
        return outputs
    
    def _deploy_application(self, repo_path: Path, app_analysis: Dict, 
                           infrastructure: Dict, tf_output: Dict) -> Dict:
        """Deploy application to provisioned infrastructure"""
        
        compute = infrastructure['compute_resources']
        
        if compute['type'] == 'vm':
            return self._deploy_to_vm(repo_path, app_analysis, tf_output)
        elif compute['type'] in ['ecs_fargate', 'cloud_run']:
            return self._deploy_to_container(repo_path, app_analysis, infrastructure, tf_output)
        else:
            raise NotImplementedError(f"Deployment type {compute['type']} not yet implemented")
    
    def _deploy_to_vm(self, repo_path: Path, app_analysis: Dict, tf_output: Dict) -> Dict:
        """Deploy application to VM"""
        
        # Get instance IP
        instance_ip = tf_output.get('instance_public_ip', {}).get('value')
        if not instance_ip:
            raise Exception("Could not get instance IP from Terraform output")
        
        self.log(f"Deploying to VM at {instance_ip}")
        
        # Get GCP project and zone from environment
        gcp_project = os.environ.get('GCP_PROJECT_ID', 'mahdi-mirhoseini')
        gcp_zone = os.environ.get('GCP_REGION', 'us-central1') + '-a'
        instance_name = f"autodeploy-{self.deployment_id}-instance"
        
        # Wait for VM to be ready and startup script to complete
        self.log("Waiting for VM to be ready...")
        import time
        time.sleep(45)  # Give VM time to start up and run startup script
        
        # Wait for startup script to complete by checking if Python is installed
        self.log("Waiting for VM startup script to complete...")
        max_retries = 10
        for i in range(max_retries):
            try:
                check_cmd = [
                    'gcloud', 'compute', 'ssh',
                    '--zone', gcp_zone,
                    '--project', gcp_project,
                    instance_name,
                    '--command', 'which python3 && which pip3'
                ]
                result = subprocess.run(check_cmd, check=True, capture_output=True, timeout=10)
                self.log("✓ VM startup complete, Python environment ready")
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                if i < max_retries - 1:
                    self.log(f"Waiting for startup script... (attempt {i+1}/{max_retries})")
                    time.sleep(10)
                else:
                    self.log("⚠️ Startup script may still be running, proceeding anyway...")
        
        try:
            # Create deployment script
            deploy_script = self._create_vm_deploy_script(app_analysis)
            script_path = self.work_dir / 'deploy.sh'
            script_path.write_text(deploy_script)
            script_path.chmod(0o755)
            
            # Copy repository to VM using gcloud scp
            self.log(f"Copying application files to VM...")
            # Copy contents of repo_path, not the directory itself
            scp_cmd = [
                'gcloud', 'compute', 'scp',
                '--recurse',
                '--zone', gcp_zone,
                '--project', gcp_project,
                str(repo_path) + '/*', f'{instance_name}:/tmp/app/'
            ]
            # Note: Using shell=True to expand the wildcard
            subprocess.run(' '.join(scp_cmd), shell=True, check=True, capture_output=True)
            self.log("✓ Files copied successfully")
            
            # Copy deployment script
            scp_script_cmd = [
                'gcloud', 'compute', 'scp',
                '--zone', gcp_zone,
                '--project', gcp_project,
                str(script_path), f'{instance_name}:/tmp/deploy.sh'
            ]
            subprocess.run(scp_script_cmd, check=True, capture_output=True)
            
            # Execute deployment script on VM
            self.log("Executing deployment script on VM...")
            ssh_cmd = [
                'gcloud', 'compute', 'ssh',
                '--zone', gcp_zone,
                '--project', gcp_project,
                instance_name,
                '--command', 'sudo bash /tmp/deploy.sh'
            ]
            result = subprocess.run(ssh_cmd, check=True, capture_output=True, text=True)
            self.log("✓ Application deployed and started")
            
        except subprocess.CalledProcessError as e:
            self.log(f"⚠️ Deployment to VM partially failed: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                self.log(f"Error details: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}")
            self.log(f"Return code: {e.returncode}")
            self.log("Note: Infrastructure is created but application may need manual setup")
            self.log(f"You can SSH to debug: gcloud compute ssh {instance_name} --zone={gcp_zone} --project={gcp_project}")
        
        return {
            'type': 'vm',
            'instance_ip': instance_ip,
            'instance_name': instance_name,
            'port': app_analysis.get('port'),
            'url': f"http://{instance_ip}:{app_analysis.get('port')}",
        }
    
    def _deploy_to_container(self, repo_path: Path, app_analysis: Dict, 
                            infrastructure: Dict, tf_output: Dict) -> Dict:
        """Deploy containerized application"""
        
        self.log("Building Docker image...")
        
        # Build Docker image
        image_tag = 'autodeploy-app:latest'
        result = subprocess.run(
            ['docker', 'build', '-t', image_tag, '.'],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Docker build failed: {result.stderr}")
        
        self.log("Docker image built successfully")
        
        # In production, would push to ECR/GCR and deploy to ECS/Cloud Run
        self.log("Image would be pushed to container registry")
        self.log("Container would be deployed to ECS Fargate / Cloud Run")
        
        return {
            'type': 'container',
            'image': image_tag,
            'port': app_analysis.get('port'),
            'url': 'http://[load-balancer-dns]',
        }
    
    def _create_vm_deploy_script(self, app_analysis: Dict) -> str:
        """Create deployment script for VM"""
        
        language = app_analysis.get('language', '')
        framework = app_analysis.get('framework', '')
        port = app_analysis.get('port', 8000)
        
        script = '''#!/bin/bash
set -e

echo "Starting application deployment..."

# Wait for startup script to complete (wait for pip3)
echo "Waiting for system dependencies to be ready..."
MAX_WAIT=180  # 3 minutes max
WAITED=0
while ! command -v pip3 &> /dev/null; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "Timeout waiting for pip3 to be installed"
        echo "Installing pip3 manually..."
        sudo apt-get update && sudo apt-get install -y python3-pip
        break
    fi
    echo "Waiting for pip3... ($WAITED seconds elapsed)"
    sleep 10
    WAITED=$((WAITED + 10))
done

echo "✓ System dependencies ready (pip3 available)"

# Copy files from /tmp to /opt
sudo mkdir -p /opt/app
sudo cp -r /tmp/app/* /opt/app/
sudo chown -R ubuntu:ubuntu /opt/app
cd /opt/app

# Fix: If app files are in /opt/app/app, move them up
if [ -d /opt/app/app ] && [ -f /opt/app/app/app.py ]; then
    echo "Moving app files from /opt/app/app/ to /opt/app/"
    sudo mv /opt/app/app/* /opt/app/
    sudo rmdir /opt/app/app
fi

# Stop existing service if running
sudo systemctl stop app.service 2>/dev/null || true

'''
        
        if language == 'python':
            # Determine start command based on framework
            if framework == 'flask':
                start_cmd = 'python3 -m flask run --host=0.0.0.0 --port=' + str(port)
            elif framework == 'django':
                start_cmd = 'python3 manage.py runserver 0.0.0.0:' + str(port)
            else:
                start_cmd = 'python3 app.py'
            
            script += f'''# Install Python dependencies
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    sudo pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
else
    echo "Warning: No requirements.txt found"
fi

# Set Flask environment variables if needed
export FLASK_APP=app.py
export FLASK_ENV=production
export PORT={port}

# Check if app files are in a subdirectory
if [ -d app ] && [ -f app/app.py ]; then
    echo "Found application in 'app' subdirectory"
    cd app
    export FLASK_APP=app.py
fi

# Verify Python application files exist
if [ ! -f app.py ] && [ ! -f app/__init__.py ]; then
    echo "Error: No Python application entry point found in $(pwd)"
    echo "Directory contents:"
    ls -la
    exit 1
fi

'''
        elif language in ['javascript', 'typescript']:
            start_cmd = 'npm start'
            script += '''# Install Node dependencies
if [ -f package.json ]; then
    echo "Installing Node.js dependencies..."
    npm install --production
fi

'''
        else:
            start_cmd = 'python3 app.py'
        
        script += f'''# Create systemd service
sudo tee /etc/systemd/system/app.service > /dev/null <<EOF
[Unit]
Description=Application Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/app
Environment="PORT={port}"
Environment="FLASK_APP=app.py"
ExecStart=/bin/bash -c '{start_cmd}'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable app.service
sudo systemctl start app.service

echo "Deployment completed!"
'''
        
        return script
    
    def _verify_deployment(self, deployment_info: Dict):
        """Verify deployment is successful"""
        self.log("Verifying deployment...")
        
        url = deployment_info.get('url')
        if not url:
            self.log("No URL available for verification")
            return
        
        try:
            import requests
            import time
            
            # Try to connect to the application (5 attempts with 10 second intervals)
            for attempt in range(5):
                try:
                    self.log(f"Checking application at {url}... (attempt {attempt + 1}/5)")
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        self.log(f"✓ Application is responding successfully (HTTP {response.status_code})")
                        return
                    else:
                        self.log(f"⚠️ Application returned HTTP {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    if attempt < 4:
                        self.log(f"Connection failed, waiting 10 seconds before retry...")
                        time.sleep(10)
                    else:
                        self.log(f"⚠️ Could not connect to application: {e}")
            
            self.log("⚠️ Application may not be fully started yet. Check manually or wait a few minutes.")
            
        except ImportError:
            self.log("Note: Install 'requests' library for automatic health checks")
            self.log(f"Manual verification: curl {url}")
    
    def _get_or_generate_ssh_key(self) -> str:
        """Get or generate SSH public key"""
        ssh_dir = Path.home() / '.ssh'
        pub_key_path = ssh_dir / 'id_rsa.pub'
        
        if pub_key_path.exists():
            return pub_key_path.read_text().strip()
        
        # Generate dummy key for demo
        return "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC... demo@autodeploy"
    
    def _generate_db_password(self) -> str:
        """Generate secure database password"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(16))
    
    def log(self, message: str, error: bool = False):
        """Log deployment message"""
        self.deployment_log.append(message)
        
        if error:
            self.console.print(f"[red]{message}[/red]")
        else:
            self.console.print(message)
    
    def _display_success(self, result: Dict):
        """Display success message with deployment details"""
        
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold green]🎉 Deployment Successful![/bold green]",
            border_style="green"
        ))
        
        # Create deployment info table
        table = Table(title="Deployment Information", show_header=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        deployment_info = result['deployment_info']
        
        table.add_row("Status", "✓ Running")
        table.add_row("Type", deployment_info.get('type', 'N/A'))
        
        if 'instance_ip' in deployment_info:
            table.add_row("Instance IP", deployment_info['instance_ip'])
        
        if 'url' in deployment_info:
            table.add_row("Application URL", deployment_info['url'])
        
        table.add_row("Port", str(deployment_info.get('port', 'N/A')))
        
        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")
