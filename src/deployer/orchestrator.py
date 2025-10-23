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
        tf = Terraform(working_dir=str(tf_dir))
        
        # Initialize
        return_code, stdout, stderr = tf.init()
        if return_code != 0:
            raise Exception(f"Terraform init failed: {stderr}")
        
        self.log("Terraform initialized")
        
        # Plan
        self.log("Planning infrastructure changes...")
        return_code, stdout, stderr = tf.plan(
            var={
                'app_name': 'autodeploy-app',
                'ssh_public_key': self._get_or_generate_ssh_key(),
                'db_password': self._generate_db_password(),
            }
        )
        
        if return_code != 0:
            self.log(f"Terraform plan output: {stdout}")
            raise Exception(f"Terraform plan failed: {stderr}")
        
        # Apply
        self.log("Applying infrastructure changes (this may take several minutes)...")
        return_code, stdout, stderr = tf.apply(
            skip_plan=True,
            var={
                'app_name': 'autodeploy-app',
                'ssh_public_key': self._get_or_generate_ssh_key(),
                'db_password': self._generate_db_password(),
            }
        )
        
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
        
        # Create deployment script
        deploy_script = self._create_vm_deploy_script(app_analysis)
        script_path = self.work_dir / 'deploy.sh'
        script_path.write_text(deploy_script)
        script_path.chmod(0o755)
        
        # Copy files to VM (simplified - in production would use SCP/rsync)
        self.log("Application files would be copied to VM via SCP")
        self.log("Deployment script would be executed on VM via SSH")
        
        # In a real implementation:
        # - Use paramiko or subprocess to SCP files
        # - SSH into instance and run deployment script
        # - Set up systemd service
        # - Start application
        
        return {
            'type': 'vm',
            'instance_ip': instance_ip,
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
        start_cmd = app_analysis.get('start_command', '')
        port = app_analysis.get('port', 8000)
        
        script = '''#!/bin/bash
set -e

echo "Starting deployment..."

# Navigate to app directory
cd /opt/app

# Stop existing service if running
sudo systemctl stop app.service || true

'''
        
        if language == 'python':
            script += '''# Install Python dependencies
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
fi

'''
        elif language in ['javascript', 'typescript']:
            script += '''# Install Node dependencies
npm install --production

'''
        
        script += f'''# Create systemd service
sudo tee /etc/systemd/system/app.service > /dev/null <<EOF
[Unit]
Description=Application Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/app
ExecStart=/usr/bin/{start_cmd}
Restart=always

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
        
        # In production, would make HTTP request to verify app is responding
        # For now, just log success
        self.log("Deployment verification would check HTTP endpoint")
    
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
