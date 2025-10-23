"""
Terraform Template Generator - Generates infrastructure as code
"""
import os
from pathlib import Path
from typing import Dict
from jinja2 import Template


class TerraformGenerator:
    """Generates Terraform configurations for different cloud providers"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self, infrastructure: Dict, app_analysis: Dict) -> Path:
        """Generate Terraform configuration"""
        provider = infrastructure['provider']
        strategy = infrastructure['deployment_strategy']
        
        # Generate main.tf
        main_tf = self._generate_main(infrastructure, app_analysis)
        (self.output_dir / 'main.tf').write_text(main_tf)
        
        # Generate variables.tf
        variables_tf = self._generate_variables(infrastructure)
        (self.output_dir / 'variables.tf').write_text(variables_tf)
        
        # Generate outputs.tf
        outputs_tf = self._generate_outputs(infrastructure)
        (self.output_dir / 'outputs.tf').write_text(outputs_tf)
        
        # Generate provider-specific files
        if provider == 'aws':
            self._generate_aws_specific(infrastructure, app_analysis)
        
        return self.output_dir
    
    def _generate_main(self, infrastructure: Dict, app_analysis: Dict) -> str:
        """Generate main Terraform configuration"""
        provider = infrastructure['provider']
        
        if provider == 'aws':
            return self._generate_aws_main(infrastructure, app_analysis)
        elif provider == 'gcp':
            return self._generate_gcp_main(infrastructure, app_analysis)
        else:
            return self._generate_azure_main(infrastructure, app_analysis)
    
    def _generate_aws_main(self, infrastructure: Dict, app_analysis: Dict) -> str:
        """Generate AWS Terraform configuration"""
        
        compute = infrastructure['compute_resources']
        networking = infrastructure['networking']
        database = infrastructure['database']
        
        template = Template('''terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.app_name}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.app_name}-igw"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.app_name}-public-subnet"
  }
}

{% if networking.private_subnet %}
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name = "${var.app_name}-private-subnet"
  }
}
{% endif %}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.app_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

data "aws_availability_zones" "available" {
  state = "available"
}

# Security Group
resource "aws_security_group" "app" {
  name        = "${var.app_name}-sg"
  description = "Security group for ${var.app_name}"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = {{ app_analysis.port }}
    to_port     = {{ app_analysis.port }}
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-sg"
  }
}

{% if compute.type == 'vm' %}
# EC2 Instance
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_key_pair" "deployer" {
  key_name   = "${var.app_name}-key"
  public_key = var.ssh_public_key
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "{{ compute.instance_type }}"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.app.id]
  key_name               = aws_key_pair.deployer.key_name

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    app_port = {{ app_analysis.port }}
  }))

  tags = {
    Name = "${var.app_name}-instance"
  }
}

{% if compute.auto_scaling %}
# Auto Scaling Configuration
resource "aws_launch_template" "app" {
  name_prefix   = "${var.app_name}-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = "{{ compute.instance_type }}"

  vpc_security_group_ids = [aws_security_group.app.id]
  key_name               = aws_key_pair.deployer.key_name

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    app_port = {{ app_analysis.port }}
  }))

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.app_name}-asg-instance"
    }
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "${var.app_name}-asg"
  vpc_zone_identifier = [aws_subnet.public.id]
  min_size            = {{ compute.count }}
  max_size            = {{ compute.max_count }}
  desired_capacity    = {{ compute.count }}

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.app_name}-asg"
    propagate_at_launch = true
  }
}
{% endif %}
{% endif %}

{% if database.required %}
# Database Security Group
resource "aws_security_group" "database" {
  name        = "${var.app_name}-db-sg"
  description = "Security group for database"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = {% if database.type == 'postgresql' %}5432{% elif database.type == 'mysql' %}3306{% else %}27017{% endif %}
    to_port         = {% if database.type == 'postgresql' %}5432{% elif database.type == 'mysql' %}3306{% else %}27017{% endif %}
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-db-sg"
  }
}

# RDS Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-db-subnet"
  subnet_ids = [aws_subnet.public.id{% if networking.private_subnet %}, aws_subnet.private.id{% endif %}]

  tags = {
    Name = "${var.app_name}-db-subnet-group"
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier           = "${var.app_name}-db"
  engine               = "{{ database.type }}"
  engine_version       = "{{ database.engine_version }}"
  instance_class       = "{{ database.instance_class }}"
  allocated_storage    = {{ database.storage }}
  storage_type         = "gp2"
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  
  backup_retention_period = {{ database.backup_retention }}
  skip_final_snapshot     = true
  publicly_accessible     = false

  tags = {
    Name = "${var.app_name}-database"
  }
}
{% endif %}

{% if networking.load_balancer %}
# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.app_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.app.id]
  subnets            = [aws_subnet.public.id]

  tags = {
    Name = "${var.app_name}-alb"
  }
}

resource "aws_lb_target_group" "app" {
  name     = "${var.app_name}-tg"
  port     = {{ app_analysis.port }}
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id

  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 60
    interval            = 300
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

{% if compute.type == 'vm' %}
resource "aws_lb_target_group_attachment" "app" {
  target_group_arn = aws_lb_target_group.app.arn
  target_id        = aws_instance.app.id
  port             = {{ app_analysis.port }}
}
{% endif %}
{% endif %}
''')
        
        return template.render(
            compute=compute,
            networking=networking,
            database=database,
            app_analysis=app_analysis
        )
    
    def _generate_gcp_main(self, infrastructure: Dict, app_analysis: Dict) -> str:
        """Generate GCP Terraform configuration"""
        return '''terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Compute Instance
resource "google_compute_instance" "app" {
  name         = "${var.app_name}-instance"
  machine_type = "e2-micro"
  zone         = "${var.gcp_region}-a"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral public IP
    }
  }

  metadata_startup_script = file("${path.module}/startup_script.sh")

  tags = ["http-server", "https-server"]
}

# Firewall rule
resource "google_compute_firewall" "app" {
  name    = "${var.app_name}-firewall"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "443", "''' + str(app_analysis.get('port', 8000)) + '''"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server", "https-server"]
}
'''
    
    def _generate_azure_main(self, infrastructure: Dict, app_analysis: Dict) -> str:
        """Generate Azure Terraform configuration"""
        return '''terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "${var.app_name}-rg"
  location = var.azure_location
}

resource "azurerm_virtual_network" "main" {
  name                = "${var.app_name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_subnet" "main" {
  name                 = "${var.app_name}-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}
'''
    
    def _generate_variables(self, infrastructure: Dict) -> str:
        """Generate variables.tf"""
        provider = infrastructure['provider']
        
        if provider == 'aws':
            return '''variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Application name"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key for EC2 access"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "appdb"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
'''
        elif provider == 'gcp':
            return '''variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "app_name" {
  description = "Application name"
  type        = string
}
'''
        else:
            return '''variable "azure_location" {
  description = "Azure location"
  type        = string
  default     = "East US"
}

variable "app_name" {
  description = "Application name"
  type        = string
}
'''
    
    def _generate_outputs(self, infrastructure: Dict) -> str:
        """Generate outputs.tf"""
        provider = infrastructure['provider']
        networking = infrastructure['networking']
        database = infrastructure['database']
        
        outputs = []
        
        if provider == 'aws':
            if networking.get('load_balancer'):
                outputs.append('''output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}''')
            else:
                outputs.append('''output "instance_public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.app.public_ip
}''')
            
            if database.get('required'):
                outputs.append('''
output "database_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}''')
        
        elif provider == 'gcp':
            outputs.append('''output "instance_public_ip" {
  description = "Public IP of the instance"
  value       = google_compute_instance.app.network_interface[0].access_config[0].nat_ip
}''')
        
        return '\n'.join(outputs) if outputs else '# No outputs defined'
    
    def _generate_aws_specific(self, infrastructure: Dict, app_analysis: Dict):
        """Generate AWS-specific files"""
        
        # Generate user_data.sh for EC2
        user_data = self._generate_user_data(app_analysis)
        (self.output_dir / 'user_data.sh').write_text(user_data)
    
    def _generate_user_data(self, app_analysis: Dict) -> str:
        """Generate user data script for EC2"""
        
        framework = app_analysis.get('framework', '')
        language = app_analysis.get('language', '')
        
        script = '''#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install basic tools
apt-get install -y git curl wget unzip

'''
        
        if language == 'python':
            script += '''# Install Python and pip
apt-get install -y python3 python3-pip python3-venv

# Create app directory
mkdir -p /opt/app
cd /opt/app

# Install application (will be done by deployment script)
'''
        
        elif language in ['javascript', 'typescript']:
            script += '''# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Create app directory
mkdir -p /opt/app
cd /opt/app
'''
        
        script += '''
# Create systemd service (will be configured by deployment script)
echo "User data script completed"
'''
        
        return script
