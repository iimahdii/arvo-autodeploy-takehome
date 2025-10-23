"""
Infrastructure Decision Engine - Determines optimal deployment strategy
"""
from typing import Dict, List
from dataclasses import dataclass, asdict


@dataclass
class InfrastructureDecision:
    """Infrastructure deployment decision"""
    provider: str
    deployment_strategy: str
    compute_resources: Dict
    networking: Dict
    storage: Dict
    database: Dict
    additional_services: List[Dict]
    estimated_cost: str
    reasoning: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class InfrastructureDecisionEngine:
    """Determines optimal infrastructure configuration"""
    
    def __init__(self):
        self.cost_estimates = {
            'aws': {
                't2.micro': '$8.50/month',
                't2.small': '$17/month',
                't2.medium': '$34/month',
                'rds.t3.micro': '$15/month',
                'elasticache.t3.micro': '$12/month',
            },
            'gcp': {
                'e2-micro': '$6/month',
                'e2-small': '$13/month',
                'e2-medium': '$27/month',
            }
        }
    
    def decide(self, app_analysis: Dict, requirements: Dict) -> InfrastructureDecision:
        """Make infrastructure decisions based on analysis and requirements"""
        
        provider = requirements['cloud_provider']
        deployment_type = requirements['deployment_type']
        
        # Determine compute resources
        compute = self._decide_compute(app_analysis, requirements)
        
        # Determine networking
        networking = self._decide_networking(requirements)
        
        # Determine storage
        storage = self._decide_storage(app_analysis)
        
        # Determine database
        database = self._decide_database(app_analysis, requirements)
        
        # Additional services
        additional = self._decide_additional_services(app_analysis, requirements)
        
        # Estimate cost
        cost = self._estimate_cost(provider, compute, database, additional)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(app_analysis, requirements, deployment_type)
        
        return InfrastructureDecision(
            provider=provider,
            deployment_strategy=deployment_type,
            compute_resources=compute,
            networking=networking,
            storage=storage,
            database=database,
            additional_services=additional,
            estimated_cost=cost,
            reasoning=reasoning
        )
    
    def _decide_compute(self, app_analysis: Dict, requirements: Dict) -> Dict:
        """Decide compute resources"""
        deployment_type = requirements['deployment_type']
        provider = requirements['cloud_provider']
        
        if deployment_type == 'vm':
            instance_type = requirements.get('instance_type', 't2.micro')
            
            return {
                'type': 'vm',
                'instance_type': instance_type,
                'count': requirements['scaling']['min'],
                'max_count': requirements['scaling']['max'],
                'auto_scaling': requirements['scaling']['auto'],
                'os': 'ubuntu-22.04',
                'disk_size': 20,  # GB
            }
        
        elif deployment_type == 'container':
            if provider == 'aws':
                return {
                    'type': 'ecs_fargate',
                    'cpu': '256',  # 0.25 vCPU
                    'memory': '512',  # MB
                    'count': requirements['scaling']['min'],
                    'max_count': requirements['scaling']['max'],
                    'auto_scaling': requirements['scaling']['auto'],
                }
            else:
                return {
                    'type': 'cloud_run',
                    'cpu': '1',
                    'memory': '512Mi',
                    'min_instances': requirements['scaling']['min'],
                    'max_instances': requirements['scaling']['max'],
                }
        
        elif deployment_type == 'kubernetes':
            return {
                'type': 'kubernetes',
                'cluster_type': 'eks' if provider == 'aws' else 'gke',
                'node_count': 2,
                'node_type': 't3.small' if provider == 'aws' else 'e2-small',
                'pod_replicas': requirements['scaling']['min'],
            }
        
        else:  # serverless
            return {
                'type': 'serverless',
                'function_type': 'lambda' if provider == 'aws' else 'cloud_function',
                'memory': 512,
                'timeout': 30,
            }
    
    def _decide_networking(self, requirements: Dict) -> Dict:
        """Decide networking configuration"""
        return {
            'vpc': True,
            'public_subnet': True,
            'private_subnet': requirements.get('requires_database', False),
            'load_balancer': requirements['scaling']['auto'] or requirements['scaling']['max'] > 1,
            'ssl': requirements.get('ssl_required', False),
            'custom_domain': requirements.get('custom_domain'),
        }
    
    def _decide_storage(self, app_analysis: Dict) -> Dict:
        """Decide storage requirements"""
        has_static = app_analysis.get('static_files', False)
        
        return {
            'object_storage': has_static,
            'bucket_name': 'app-static-files' if has_static else None,
            'volume_size': 20,  # GB for persistent storage
        }
    
    def _decide_database(self, app_analysis: Dict, requirements: Dict) -> Dict:
        """Decide database configuration"""
        if not app_analysis.get('requires_database'):
            return {'required': False}
        
        db_type = app_analysis.get('database_type', 'postgresql')
        provider = requirements['cloud_provider']
        
        config = {
            'required': True,
            'type': db_type,
            'engine_version': self._get_db_version(db_type),
            'instance_class': 'db.t3.micro' if provider == 'aws' else 'db-f1-micro',
            'storage': 20,  # GB
            'backup_retention': 7,  # days
            'multi_az': False,  # Single AZ for cost savings
        }
        
        return config
    
    def _decide_additional_services(self, app_analysis: Dict, requirements: Dict) -> List[Dict]:
        """Decide additional services needed"""
        services = []
        
        # Redis/ElastiCache
        if app_analysis.get('requires_redis'):
            services.append({
                'type': 'redis',
                'service': 'elasticache' if requirements['cloud_provider'] == 'aws' else 'memorystore',
                'node_type': 'cache.t3.micro',
                'num_nodes': 1,
            })
        
        # CloudWatch/Monitoring
        services.append({
            'type': 'monitoring',
            'service': 'cloudwatch' if requirements['cloud_provider'] == 'aws' else 'cloud_monitoring',
            'log_retention': 7,  # days
        })
        
        return services
    
    def _get_db_version(self, db_type: str) -> str:
        """Get recommended database version"""
        versions = {
            'postgresql': '14.7',
            'mysql': '8.0',
            'mongodb': '6.0',
        }
        return versions.get(db_type, '14.7')
    
    def _estimate_cost(self, provider: str, compute: Dict, database: Dict, 
                       additional: List[Dict]) -> str:
        """Estimate monthly cost"""
        total = 0
        
        # Compute cost
        if compute['type'] == 'vm':
            instance_cost = 8.50 if 'micro' in compute['instance_type'] else 17.0
            total += instance_cost * compute['count']
        elif compute['type'] in ['ecs_fargate', 'cloud_run']:
            total += 15  # Estimated for small container
        elif compute['type'] == 'kubernetes':
            total += 50  # Estimated for small cluster
        else:
            total += 5  # Serverless
        
        # Database cost
        if database.get('required'):
            total += 15
        
        # Additional services
        for service in additional:
            if service['type'] == 'redis':
                total += 12
            elif service['type'] == 'monitoring':
                total += 5
        
        return f"${total:.2f}/month (estimated)"
    
    def _generate_reasoning(self, app_analysis: Dict, requirements: Dict, 
                           deployment_type: str) -> str:
        """Generate human-readable reasoning for decisions"""
        reasons = []
        
        # App type reasoning
        app_type = app_analysis.get('app_type', 'unknown')
        framework = app_analysis.get('framework', 'unknown')
        reasons.append(f"Detected {framework or app_type} application")
        
        # Deployment strategy reasoning
        if deployment_type == 'vm':
            reasons.append("Using VM deployment for simplicity and full control")
        elif deployment_type == 'container':
            reasons.append("Using containerized deployment for better isolation and scalability")
        elif deployment_type == 'kubernetes':
            reasons.append("Using Kubernetes for complex multi-service architecture")
        else:
            reasons.append("Using serverless for cost-effective, auto-scaling deployment")
        
        # Database reasoning
        if app_analysis.get('requires_database'):
            db_type = app_analysis.get('database_type', 'postgresql')
            reasons.append(f"Provisioning managed {db_type} database for data persistence")
        
        # Scaling reasoning
        if requirements['scaling']['auto']:
            reasons.append("Configured auto-scaling for handling variable traffic")
        
        return ". ".join(reasons) + "."
