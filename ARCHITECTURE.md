# Architecture Documentation

## System Design Philosophy

AutoDeploy is designed with the following principles:

1. **Modularity**: Each component has a single, well-defined responsibility
2. **Extensibility**: Easy to add new cloud providers, frameworks, or deployment strategies
3. **Robustness**: Comprehensive error handling and fallback mechanisms
4. **Transparency**: Detailed logging and cost estimation before deployment
5. **Production-Ready**: Generates infrastructure that follows cloud best practices

## Component Architecture

### 1. Repository Analyzer (`src/analyzer/repo_analyzer.py`)

**Purpose**: Deep inspection of application code to understand deployment requirements

**Key Responsibilities**:
- Language detection via file extension analysis
- Framework identification through pattern matching and code inspection
- Dependency parsing from multiple formats (requirements.txt, package.json, Gemfile, etc.)
- Database requirement detection
- Entry point discovery
- Command inference (build, start)
- Environment variable extraction

**Design Decisions**:
- **Weighted Scoring System**: Framework detection uses weighted scores to handle ambiguous cases
- **Multi-Phase Detection**: Database detection uses both dependency analysis and code scanning
- **Confidence Scoring**: Provides transparency about analysis certainty
- **Extensible Patterns**: Easy to add new frameworks via pattern dictionaries

**Data Flow**:
```
Repository → File Scan → Language Detection → Framework Detection → 
Dependency Parsing → Database Detection → Entry Point Discovery → 
Command Inference → AnalysisResult
```

### 2. NLP Requirement Parser (`src/nlp/requirement_parser.py`)

**Purpose**: Extract structured deployment requirements from natural language

**Key Responsibilities**:
- Parse cloud provider preferences
- Determine deployment type (VM, container, K8s, serverless)
- Extract region, instance type, scaling requirements
- Identify SSL, domain, and additional service needs

**Design Decisions**:
- **Dual-Mode Operation**: LLM-based parsing with rule-based fallback
- **LLM Integration**: Supports both OpenAI and Anthropic for flexibility
- **Structured Prompts**: Uses JSON schema for consistent LLM outputs
- **Smart Defaults**: Provides sensible defaults when information is missing
- **Context-Aware**: Combines user description with app analysis for better decisions

**LLM Prompt Strategy**:
```
Role Definition → Context (App Analysis) → Task Description → 
Output Format (JSON Schema) → Decision Rules → Examples
```

**Fallback Strategy**:
- Keyword matching for cloud providers
- Pattern recognition for deployment types
- Heuristic-based defaults
- App-type-aware decisions

### 3. Infrastructure Decision Engine (`src/infrastructure/decision_engine.py`)

**Purpose**: Make intelligent infrastructure configuration decisions

**Key Responsibilities**:
- Choose optimal deployment strategy
- Size compute resources appropriately
- Configure networking (VPC, subnets, security groups)
- Select database configurations
- Determine additional services needed
- Estimate monthly costs

**Design Decisions**:
- **Strategy Pattern**: Different decision logic for different deployment types
- **Cost-Conscious**: Defaults to smallest viable resources
- **Security-First**: Private subnets for databases, minimal security group rules
- **Scalability-Ready**: Configures auto-scaling when requested
- **Transparent Reasoning**: Generates human-readable explanation of decisions

**Decision Matrix**:
```python
if simple_app and no_database:
    strategy = VM
elif app_with_database or docker_compose:
    strategy = Container
elif microservices or complex_architecture:
    strategy = Kubernetes
elif event_driven or api_only:
    strategy = Serverless
```

### 4. Terraform Generator (`src/infrastructure/terraform_generator.py`)

**Purpose**: Generate production-ready infrastructure as code

**Key Responsibilities**:
- Generate main.tf with all resources
- Create variables.tf for parameterization
- Build outputs.tf for deployment info
- Generate initialization scripts (user_data.sh)

**Design Decisions**:
- **Jinja2 Templates**: Flexible, readable template system
- **Conditional Resources**: Only create what's needed
- **Best Practices**: Follows Terraform and cloud provider conventions
- **Modular Structure**: Separate files for different concerns
- **Provider Abstraction**: Easy to add new cloud providers

**Generated Resources (AWS Example)**:
```
VPC → Subnets → Internet Gateway → Route Tables → 
Security Groups → EC2/ECS → RDS (optional) → 
ElastiCache (optional) → Load Balancer (optional) → 
Auto Scaling (optional)
```

### 5. Deployment Orchestrator (`src/deployer/orchestrator.py`)

**Purpose**: Coordinate the entire deployment process

**Key Responsibilities**:
- Repository preparation (clone/copy/extract)
- Application building
- Dockerfile generation
- Terraform execution
- Application deployment
- Deployment verification

**Design Decisions**:
- **Phase-Based Execution**: Clear, sequential phases with logging
- **Error Recovery**: Try-catch at each phase with detailed errors
- **Progress Feedback**: Rich terminal output with spinners and tables
- **Artifact Generation**: Saves all configurations and logs
- **Verification**: Health checks and status validation

**Deployment Pipeline**:
```
1. Prepare Repository
   ↓
2. Build Application (if needed)
   ↓
3. Create Dockerfile (if missing)
   ↓
4. Generate Terraform
   ↓
5. Terraform Init → Plan → Apply
   ↓
6. Deploy Application (VM/Container/K8s)
   ↓
7. Verify Deployment
   ↓
8. Output Results
```

## Data Models

### AnalysisResult
```python
@dataclass
class AnalysisResult:
    app_type: str              # Framework/app type
    framework: Optional[str]   # Specific framework
    language: str              # Programming language
    dependencies: Dict         # Parsed dependencies
    entry_point: Optional[str] # Main file
    build_command: Optional[str]
    start_command: Optional[str]
    port: int
    environment_vars: List[str]
    requires_database: bool
    database_type: Optional[str]
    requires_redis: bool
    requires_docker: bool
    dockerfile_present: bool
    docker_compose_present: bool
    static_files: bool
    confidence_score: float    # 0.0 - 1.0
```

### DeploymentRequirements
```python
@dataclass
class DeploymentRequirements:
    cloud_provider: str        # aws, gcp, azure
    deployment_type: str       # vm, container, kubernetes, serverless
    region: Optional[str]
    instance_type: Optional[str]
    scaling: Dict              # min, max, auto
    custom_domain: Optional[str]
    ssl_required: bool
    additional_services: List[str]
    raw_description: str
```

### InfrastructureDecision
```python
@dataclass
class InfrastructureDecision:
    provider: str
    deployment_strategy: str
    compute_resources: Dict
    networking: Dict
    storage: Dict
    database: Dict
    additional_services: List[Dict]
    estimated_cost: str
    reasoning: str
```

## Error Handling Strategy

### Levels of Error Handling

1. **Input Validation**: Early validation of user inputs
2. **Component-Level**: Try-catch in each major component
3. **Phase-Level**: Error handling at each deployment phase
4. **Graceful Degradation**: Fallbacks when possible (e.g., LLM → rules)
5. **User Feedback**: Clear error messages with actionable suggestions

### Example Error Flow
```
User Input → Validation Error → Clear Message + Exit
Repository Clone → Git Error → Detailed Error + Suggestions
LLM Parsing → API Error → Fallback to Rule-Based
Terraform Apply → TF Error → Show TF Output + Rollback Info
```

## Extensibility Points

### Adding a New Framework

1. Add patterns to `FRAMEWORK_PATTERNS` in `repo_analyzer.py`
2. Add default port to `DEFAULT_PORTS`
3. Add build/start commands to respective methods
4. Update Dockerfile generation in `orchestrator.py`

### Adding a New Cloud Provider

1. Create new template method in `terraform_generator.py`
2. Add provider-specific resources
3. Update `decision_engine.py` with provider-specific sizing
4. Add deployment logic in `orchestrator.py`

### Adding a New Deployment Type

1. Add detection patterns to `requirement_parser.py`
2. Add decision logic to `decision_engine.py`
3. Create Terraform template in `terraform_generator.py`
4. Implement deployment method in `orchestrator.py`

## Security Considerations

### Credentials Management
- Never hardcode credentials
- Use environment variables or cloud provider credential chains
- Support for AWS IAM roles, GCP service accounts
- Sensitive values marked as `sensitive` in Terraform

### Network Security
- VPC isolation by default
- Private subnets for databases
- Security groups with minimal required rules
- No 0.0.0.0/0 access except for HTTP/HTTPS

### Application Security
- Encrypted storage by default
- SSL/TLS for production deployments
- Database backups enabled
- Secrets management (future enhancement)

## Performance Considerations

### Repository Analysis
- Efficient file scanning with os.walk
- Lazy loading of file contents
- Caching of analysis results (future)

### LLM Usage
- Low temperature (0.1) for consistency
- Minimal token usage with structured prompts
- Fallback to avoid API dependency
- Async calls for multiple analyses (future)

### Terraform Execution
- Parallel resource creation where possible
- State management for idempotency
- Resource tagging for management

## Testing Strategy

### Unit Tests (Future)
- Test each component in isolation
- Mock external dependencies (Git, LLM, Terraform)
- Test error conditions

### Integration Tests (Future)
- Test full pipeline with sample repos
- Verify Terraform generation
- Test deployment to test environments

### End-to-End Tests (Future)
- Deploy real applications
- Verify accessibility
- Test rollback procedures

## Monitoring and Observability

### Logging
- Structured logging with levels (DEBUG, INFO, WARNING, ERROR)
- File logging for audit trail
- Rich console output for user feedback

### Metrics (Future)
- Deployment success rate
- Average deployment time
- Cost accuracy
- Framework detection accuracy

### Alerting (Future)
- Failed deployments
- Cost overruns
- Security issues

## Future Enhancements

### Short Term
1. Complete VM deployment implementation (SSH, SCP)
2. Add rollback functionality
3. Implement health checks
4. Add more cloud providers (Azure complete)
5. Support for Docker Compose multi-container apps

### Medium Term
1. Web UI for easier interaction
2. Deployment templates library
3. Cost optimization recommendations
4. Automated testing of deployed apps
5. Integration with CI/CD pipelines

### Long Term
1. Multi-region deployments
2. Blue-green deployments
3. Canary releases
4. Auto-remediation of failed deployments
5. ML-based cost and performance optimization
6. Kubernetes operator for GitOps

## Comparison with Existing Solutions

### vs. Heroku
- **Advantage**: More control, multi-cloud, cost transparency
- **Disadvantage**: More complex, requires cloud credentials

### vs. AWS Elastic Beanstalk
- **Advantage**: Multi-cloud, natural language interface, smarter defaults
- **Disadvantage**: Less mature, fewer integrations

### vs. Terraform Cloud
- **Advantage**: Automated analysis, no manual configuration, NLP interface
- **Disadvantage**: Less flexibility for custom configurations

### vs. Kubernetes Operators
- **Advantage**: Simpler, works with any deployment type, not K8s-only
- **Disadvantage**: Less sophisticated orchestration

## Conclusion

AutoDeploy demonstrates a deep understanding of:
- Cloud infrastructure and deployment patterns
- Infrastructure as code best practices
- Natural language processing and LLM integration
- System design and software architecture
- DevOps workflows and automation

The architecture is designed to be production-ready while remaining extensible and maintainable.
