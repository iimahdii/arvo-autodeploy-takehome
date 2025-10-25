"""
NLP Requirement Parser - Extracts deployment requirements from natural language
"""
import re
import os
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from openai import OpenAI
from anthropic import Anthropic

# Google Vertex AI
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False


@dataclass
class DeploymentRequirements:
    """Parsed deployment requirements"""
    cloud_provider: str  # aws, gcp, azure
    deployment_type: str  # serverless, vm, container, kubernetes
    region: Optional[str]
    instance_type: Optional[str]
    scaling: Dict[str, any]
    custom_domain: Optional[str]
    ssl_required: bool
    additional_services: List[str]
    raw_description: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class RequirementParser:
    """Parses natural language deployment requirements using LLMs"""
    
    CLOUD_PROVIDERS = {
        'aws': ['aws', 'amazon', 'ec2', 'lambda', 'ecs', 'fargate'],
        'gcp': ['gcp', 'google cloud', 'gce', 'cloud run', 'app engine'],
        'azure': ['azure', 'microsoft', 'azure vm', 'azure functions'],
    }
    
    DEPLOYMENT_TYPES = {
        'serverless': ['serverless', 'lambda', 'function', 'cloud run', 'cloud functions'],
        'vm': ['vm', 'virtual machine', 'ec2', 'compute engine', 'instance'],
        'container': ['container', 'docker', 'ecs', 'fargate'],
        'kubernetes': ['kubernetes', 'k8s', 'eks', 'gke', 'aks'],
    }
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.vertex_model = None
        
        # Initialize Vertex AI (Google Cloud) - PRIORITY if GCP credentials exist
        if VERTEX_AVAILABLE and os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            try:
                gcp_project = os.getenv('GCP_PROJECT_ID', 'mahdi-mirhoseini')
                gcp_region = os.getenv('GCP_REGION', 'us-central1')
                vertexai.init(project=gcp_project, location=gcp_region)
                self.vertex_model = GenerativeModel('gemini-1.5-flash')
                print(f"✓ Vertex AI initialized (project: {gcp_project})")
            except Exception as e:
                print(f"Vertex AI initialization failed: {e}")
        
        # Initialize OpenAI (fallback)
        if os.getenv('OPENAI_API_KEY'):
            self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            print("✓ OpenAI client initialized")
        
        # Initialize Anthropic (fallback)
        if os.getenv('ANTHROPIC_API_KEY'):
            self.anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            print("✓ Anthropic client initialized")
    
    def parse(self, description: str, app_analysis: Dict) -> DeploymentRequirements:
        """Parse natural language deployment requirements"""
        
        # Try LLM-based parsing first (more accurate)
        if self.vertex_model or self.openai_client or self.anthropic_client:
            try:
                return self._parse_with_llm(description, app_analysis)
            except Exception as e:
                print(f"LLM parsing failed: {e}, falling back to rule-based parsing")
        
        # Fallback to rule-based parsing
        return self._parse_with_rules(description, app_analysis)
    
    def _parse_with_llm(self, description: str, app_analysis: Dict) -> DeploymentRequirements:
        """Parse using LLM for better understanding"""
        
        prompt = f"""You are a DevOps expert. Parse the following deployment request and application analysis into structured deployment requirements.

Deployment Request: "{description}"

Application Analysis:
- Type: {app_analysis.get('app_type')}
- Framework: {app_analysis.get('framework')}
- Language: {app_analysis.get('language')}
- Requires Database: {app_analysis.get('requires_database')}
- Database Type: {app_analysis.get('database_type')}
- Port: {app_analysis.get('port')}

Extract and return ONLY a JSON object with these fields:
{{
  "cloud_provider": "aws|gcp|azure",
  "deployment_type": "serverless|vm|container|kubernetes",
  "region": "region name or null",
  "instance_type": "instance type or null",
  "scaling": {{"min": 1, "max": 3, "auto": true}},
  "custom_domain": "domain or null",
  "ssl_required": true|false,
  "additional_services": ["service1", "service2"]
}}

Rules:
- If no cloud provider specified, default to "aws"
- Choose deployment_type based on app complexity:
  * Simple apps (Flask, Express) -> "vm" or "container"
  * Complex apps with DB -> "container"
  * Microservices -> "kubernetes"
- Default region: us-east-1 for AWS, us-central1 for GCP
- Instance type: t2.micro for small apps, t2.small for medium
- SSL required if domain mentioned or production deployment
- Additional services: database, redis, load_balancer, etc.

Return ONLY the JSON, no explanation."""

        try:
            # Priority: Vertex AI (same cloud, cheaper, faster)
            if self.vertex_model:
                response = self.vertex_model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.1,
                        'max_output_tokens': 500,
                    }
                )
                result = response.text.strip()
            elif self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=500
                )
                result = response.choices[0].message.content.strip()
            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.content[0].text.strip()
            else:
                raise Exception("No LLM client available")
            
            # Extract JSON from response
            import json
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                return DeploymentRequirements(
                    cloud_provider=parsed.get('cloud_provider', 'aws'),
                    deployment_type=parsed.get('deployment_type', 'container'),
                    region=parsed.get('region'),
                    instance_type=parsed.get('instance_type'),
                    scaling=parsed.get('scaling', {'min': 1, 'max': 1, 'auto': False}),
                    custom_domain=parsed.get('custom_domain'),
                    ssl_required=parsed.get('ssl_required', False),
                    additional_services=parsed.get('additional_services', []),
                    raw_description=description
                )
            else:
                raise Exception("No JSON found in LLM response")
                
        except Exception as e:
            raise Exception(f"LLM parsing error: {e}")
    
    def _parse_with_rules(self, description: str, app_analysis: Dict) -> DeploymentRequirements:
        """Fallback rule-based parsing"""
        
        desc_lower = description.lower()
        
        # Detect cloud provider
        cloud_provider = 'aws'  # default
        for provider, keywords in self.CLOUD_PROVIDERS.items():
            if any(kw in desc_lower for kw in keywords):
                cloud_provider = provider
                break
        
        # Detect deployment type
        deployment_type = 'container'  # default
        for dep_type, keywords in self.DEPLOYMENT_TYPES.items():
            if any(kw in desc_lower for kw in keywords):
                deployment_type = dep_type
                break
        
        # Smart deployment type selection based on app
        if deployment_type == 'container':
            if app_analysis.get('requires_database') or app_analysis.get('docker_compose_present'):
                deployment_type = 'container'
            elif app_analysis.get('app_type') in ['flask', 'fastapi', 'express']:
                deployment_type = 'vm'  # Simple apps can use VM
        
        # Detect region
        region = None
        region_patterns = {
            'us-east-1': ['us-east', 'virginia', 'us east'],
            'us-west-2': ['us-west', 'oregon', 'us west'],
            'eu-west-1': ['eu-west', 'ireland', 'europe'],
            'ap-southeast-1': ['singapore', 'asia'],
        }
        
        for reg, patterns in region_patterns.items():
            if any(p in desc_lower for p in patterns):
                region = reg
                break
        
        if not region:
            region = 'us-east-1' if cloud_provider == 'aws' else 'us-central1'
        
        # Detect instance type
        instance_type = None
        if 'small' in desc_lower or 'micro' in desc_lower:
            instance_type = 't2.micro'
        elif 'medium' in desc_lower:
            instance_type = 't2.small'
        elif 'large' in desc_lower:
            instance_type = 't2.medium'
        else:
            instance_type = 't2.micro'  # default
        
        # Detect scaling
        scaling = {'min': 1, 'max': 1, 'auto': False}
        if 'scale' in desc_lower or 'auto-scale' in desc_lower:
            scaling = {'min': 1, 'max': 3, 'auto': True}
        
        # Detect custom domain
        custom_domain = None
        domain_match = re.search(r'(?:domain|url)[:\s]+([a-z0-9.-]+\.[a-z]{2,})', desc_lower)
        if domain_match:
            custom_domain = domain_match.group(1)
        
        # SSL required
        ssl_required = 'ssl' in desc_lower or 'https' in desc_lower or custom_domain is not None
        
        # Additional services
        additional_services = []
        if app_analysis.get('requires_database'):
            db_type = app_analysis.get('database_type', 'postgresql')
            additional_services.append(f"database_{db_type}")
        
        if app_analysis.get('requires_redis'):
            additional_services.append('redis')
        
        if 'load balancer' in desc_lower or 'lb' in desc_lower:
            additional_services.append('load_balancer')
        
        return DeploymentRequirements(
            cloud_provider=cloud_provider,
            deployment_type=deployment_type,
            region=region,
            instance_type=instance_type,
            scaling=scaling,
            custom_domain=custom_domain,
            ssl_required=ssl_required,
            additional_services=additional_services,
            raw_description=description
        )
