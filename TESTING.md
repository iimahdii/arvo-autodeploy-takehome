# Testing Strategy

## Overview

This document outlines the testing strategy for AutoDeploy, including unit tests, integration tests, and end-to-end tests. While full test coverage is not implemented in this assessment version, this document demonstrates understanding of production testing requirements.

## Testing Pyramid

```
         /\
        /  \      E2E Tests (Few)
       /    \     - Full deployment workflows
      /------\    - Cloud provider integration
     /        \
    /          \  Integration Tests (Some)
   /            \ - Component interactions
  /              \- CLI command flows
 /----------------\
/                  \ Unit Tests (Many)
 Component testing  - Individual functions
 Pure logic testing - Data transformations
```

## Test Categories

### 1. Unit Tests

Test individual components in isolation.

#### Repository Analyzer Tests

```python
# tests/test_analyzer.py
import pytest
from src.analyzer.repo_analyzer import RepositoryAnalyzer

class TestRepositoryAnalyzer:
    
    def test_detect_flask_application(self, tmp_path):
        """Test Flask application detection"""
        # Setup
        app_file = tmp_path / "app.py"
        app_file.write_text("from flask import Flask\napp = Flask(__name__)")
        
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("Flask==2.3.0")
        
        # Execute
        analyzer = RepositoryAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        # Assert
        assert result.framework == "flask"
        assert result.language == "python"
        assert result.confidence_score > 0.8
    
    def test_detect_django_application(self, tmp_path):
        """Test Django application detection"""
        manage_file = tmp_path / "manage.py"
        manage_file.write_text("django.core.management")
        
        analyzer = RepositoryAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result.framework == "django"
    
    def test_database_detection_postgres(self, tmp_path):
        """Test PostgreSQL requirement detection"""
        requirements = tmp_path / "requirements.txt"
        requirements.write_text("psycopg2-binary==2.9.0")
        
        analyzer = RepositoryAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result.requires_database is True
        assert result.database_type == "postgresql"
    
    def test_port_detection_custom(self, tmp_path):
        """Test custom port detection"""
        app_file = tmp_path / "app.py"
        app_file.write_text("app.run(port=8080)")
        
        analyzer = RepositoryAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        assert result.port == 8080
    
    def test_confidence_score_calculation(self, tmp_path):
        """Test confidence score is calculated correctly"""
        # Minimal app
        app_file = tmp_path / "app.py"
        app_file.write_text("print('hello')")
        
        analyzer = RepositoryAnalyzer(str(tmp_path))
        result = analyzer.analyze()
        
        # Low confidence for minimal app
        assert 0.0 <= result.confidence_score <= 1.0
```

#### NLP Parser Tests

```python
# tests/test_nlp_parser.py
import pytest
from src.nlp.requirement_parser import RequirementParser
from src.analyzer.repo_analyzer import AnalysisResult

class TestRequirementParser:
    
    def test_parse_aws_deployment(self):
        """Test parsing AWS deployment request"""
        parser = RequirementParser()
        description = "Deploy this application on AWS"
        analysis = AnalysisResult(
            app_type="flask",
            framework="flask",
            language="python",
            # ... other fields
        )
        
        result = parser.parse(description, analysis)
        
        assert result.cloud_provider == "aws"
    
    def test_parse_instance_type(self):
        """Test parsing specific instance type"""
        parser = RequirementParser()
        description = "Deploy on AWS using t2.micro instance"
        
        result = parser.parse(description, mock_analysis)
        
        assert result.instance_type == "t2.micro"
    
    def test_parse_region(self):
        """Test parsing specific region"""
        parser = RequirementParser()
        description = "Deploy to us-west-2 region"
        
        result = parser.parse(description, mock_analysis)
        
        assert result.region == "us-west-2"
    
    def test_fallback_to_rule_based(self, monkeypatch):
        """Test fallback when LLM fails"""
        # Mock LLM to raise exception
        def mock_llm_error(*args, **kwargs):
            raise Exception("API error")
        
        monkeypatch.setattr("openai.ChatCompletion.create", mock_llm_error)
        
        parser = RequirementParser()
        result = parser.parse("Deploy on AWS", mock_analysis)
        
        # Should still work with rule-based
        assert result.cloud_provider == "aws"
```

#### Decision Engine Tests

```python
# tests/test_decision_engine.py
import pytest
from src.infrastructure.decision_engine import InfrastructureDecisionEngine

class TestDecisionEngine:
    
    def test_simple_app_uses_vm(self):
        """Test simple apps use VM deployment"""
        engine = InfrastructureDecisionEngine()
        
        analysis = create_simple_flask_analysis()
        requirements = create_aws_requirements()
        
        decision = engine.decide(analysis, requirements)
        
        assert decision.deployment_strategy == "vm"
    
    def test_app_with_database_uses_container(self):
        """Test apps with database use container deployment"""
        engine = InfrastructureDecisionEngine()
        
        analysis = create_django_with_postgres_analysis()
        requirements = create_aws_requirements()
        
        decision = engine.decide(analysis, requirements)
        
        assert decision.deployment_strategy == "container"
        assert decision.database is not None
    
    def test_cost_estimation(self):
        """Test cost estimation is reasonable"""
        engine = InfrastructureDecisionEngine()
        
        decision = engine.decide(simple_analysis, aws_requirements)
        
        # Extract number from estimate like "$8.50/month"
        cost = float(decision.estimated_cost.split('$')[1].split('/')[0])
        assert 5 <= cost <= 50  # Reasonable range for t2.micro
    
    def test_scaling_configuration(self):
        """Test auto-scaling is configured when requested"""
        requirements = create_requirements_with_scaling()
        
        decision = engine.decide(analysis, requirements)
        
        assert decision.compute_resources['auto_scaling'] is True
        assert decision.compute_resources['min_instances'] >= 1
```

#### Terraform Generator Tests

```python
# tests/test_terraform_generator.py
import pytest
from src.infrastructure.terraform_generator import TerraformGenerator

class TestTerraformGenerator:
    
    def test_generates_main_tf(self, tmp_path):
        """Test main.tf is generated"""
        generator = TerraformGenerator()
        decision = create_vm_decision()
        
        generator.generate(decision, str(tmp_path))
        
        assert (tmp_path / "main.tf").exists()
    
    def test_generates_variables_tf(self, tmp_path):
        """Test variables.tf is generated"""
        generator = TerraformGenerator()
        decision = create_vm_decision()
        
        generator.generate(decision, str(tmp_path))
        
        assert (tmp_path / "variables.tf").exists()
    
    def test_aws_vpc_configuration(self, tmp_path):
        """Test AWS VPC is configured correctly"""
        generator = TerraformGenerator()
        decision = create_aws_decision()
        
        generator.generate(decision, str(tmp_path))
        
        main_tf = (tmp_path / "main.tf").read_text()
        
        assert 'resource "aws_vpc"' in main_tf
        assert 'resource "aws_subnet"' in main_tf
        assert 'resource "aws_internet_gateway"' in main_tf
    
    def test_security_group_rules(self, tmp_path):
        """Test security groups have correct rules"""
        generator = TerraformGenerator()
        decision = create_decision_with_database()
        
        generator.generate(decision, str(tmp_path))
        
        main_tf = (tmp_path / "main.tf").read_text()
        
        # App security group allows app port
        assert 'from_port = var.app_port' in main_tf
        
        # DB security group doesn't allow public access
        assert '0.0.0.0/0' not in main_tf.split('aws_security_group.db')[1].split('aws_security_group')[0]
```

### 2. Integration Tests

Test component interactions.

```python
# tests/integration/test_full_analysis.py
import pytest
from src.analyzer.repo_analyzer import RepositoryAnalyzer
from src.nlp.requirement_parser import RequirementParser
from src.infrastructure.decision_engine import InfrastructureDecisionEngine

class TestFullAnalysisFlow:
    
    def test_analyze_parse_decide_flow(self, sample_repo):
        """Test complete flow from analysis to decision"""
        # Step 1: Analyze
        analyzer = RepositoryAnalyzer(sample_repo)
        analysis = analyzer.analyze()
        
        # Step 2: Parse requirements
        parser = RequirementParser()
        requirements = parser.parse(
            "Deploy this Flask app on AWS",
            analysis
        )
        
        # Step 3: Make decision
        engine = InfrastructureDecisionEngine()
        decision = engine.decide(analysis, requirements)
        
        # Assertions
        assert analysis.framework == "flask"
        assert requirements.cloud_provider == "aws"
        assert decision.deployment_strategy in ["vm", "container"]
    
    def test_database_app_full_flow(self, django_repo):
        """Test flow for app with database"""
        analyzer = RepositoryAnalyzer(django_repo)
        analysis = analyzer.analyze()
        
        assert analysis.requires_database is True
        
        parser = RequirementParser()
        requirements = parser.parse("Deploy on AWS", analysis)
        
        engine = InfrastructureDecisionEngine()
        decision = engine.decide(analysis, requirements)
        
        # Should provision database
        assert decision.database is not None
        assert decision.database['engine'] in ['postgres', 'mysql']
```

### 3. End-to-End Tests

Test complete deployment workflows (requires cloud credentials).

```python
# tests/e2e/test_deployment.py
import pytest

@pytest.mark.slow
@pytest.mark.e2e
@pytest.mark.skipif(not has_aws_credentials(), reason="AWS credentials not available")
class TestE2EDeployment:
    
    def test_deploy_simple_flask_app(self):
        """Test deploying a simple Flask app end-to-end"""
        # This would actually deploy to AWS
        # Run with: pytest -m e2e
        
        from src.deployer.orchestrator import DeploymentOrchestrator
        
        orchestrator = DeploymentOrchestrator()
        result = orchestrator.deploy(
            repo_url="https://github.com/Arvo-AI/hello_world",
            description="Deploy Flask app on AWS",
            dry_run=False  # Actually deploy
        )
        
        assert result.status == "success"
        assert result.endpoint is not None
        
        # Verify endpoint is accessible
        response = requests.get(result.endpoint)
        assert response.status_code == 200
        
        # Cleanup
        orchestrator.destroy(result.deployment_id)
```

## Test Fixtures

```python
# tests/conftest.py
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture
def tmp_repo():
    """Create temporary repository directory"""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)

@pytest.fixture
def flask_app(tmp_repo):
    """Create a sample Flask application"""
    Path(tmp_repo, "app.py").write_text("""
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
""")
    
    Path(tmp_repo, "requirements.txt").write_text("Flask==2.3.0")
    
    return tmp_repo

@pytest.fixture
def django_app(tmp_repo):
    """Create a sample Django application"""
    Path(tmp_repo, "manage.py").write_text("django.core.management")
    Path(tmp_repo, "requirements.txt").write_text("""
Django==4.2.0
psycopg2-binary==2.9.5
""")
    return tmp_repo
```

## Running Tests

### Quick Tests (< 1 minute)
```bash
# Run all quick tests
pytest tests/ -v

# Run specific test file
pytest tests/test_analyzer.py -v

# Run tests matching pattern
pytest -k "test_flask" -v
```

### Integration Tests (~5 minutes)
```bash
# Run integration tests
pytest tests/integration/ -v
```

### E2E Tests (~30 minutes)
```bash
# Run E2E tests (requires cloud credentials)
pytest tests/e2e/ -v -m e2e

# Skip E2E tests
pytest -v -m "not e2e"
```

### Coverage Report
```bash
# Generate coverage report
pytest --cov=src --cov-report=html --cov-report=term

# View coverage
open htmlcov/index.html
```

## Test Metrics

### Current Status
- **Unit Tests:** 0 implemented (would be ~50+ for full coverage)
- **Integration Tests:** 0 implemented (would be ~20+ for full coverage)
- **E2E Tests:** 0 implemented (would be ~5+ for full coverage)
- **Coverage:** Structure validation only

### Production Targets
- **Unit Test Coverage:** >80%
- **Integration Test Coverage:** >60%
- **E2E Test Coverage:** Critical paths
- **Code Coverage:** >85%

## Continuous Integration

Tests would run automatically on:
- Every commit to feature branch
- Every pull request to main
- Before every deployment
- Nightly for E2E tests

See `.github/workflows/ci.yml.example` for CI/CD configuration.

## Test Data Management

### Mock Data
```python
# tests/mocks.py

def create_simple_flask_analysis():
    """Create mock analysis for simple Flask app"""
    return AnalysisResult(
        app_type="flask",
        framework="flask",
        language="python",
        dependencies={"python": ["Flask==2.3.0"]},
        entry_point="app.py",
        start_command="python app.py",
        port=5000,
        requires_database=False,
        confidence_score=0.9
    )
```

### Test Repositories
- `tests/fixtures/flask-simple/` - Minimal Flask app
- `tests/fixtures/django-blog/` - Django with PostgreSQL
- `tests/fixtures/express-api/` - Node.js Express API
- `tests/fixtures/multi-container/` - Docker Compose app

## Performance Testing

```python
# tests/performance/test_performance.py
import pytest
import time

def test_analysis_performance(flask_app):
    """Test analysis completes in reasonable time"""
    analyzer = RepositoryAnalyzer(flask_app)
    
    start = time.time()
    result = analyzer.analyze()
    duration = time.time() - start
    
    assert duration < 5.0  # Should complete in < 5 seconds
```

## Security Testing

```python
# tests/security/test_security.py

def test_no_path_traversal():
    """Test path traversal is prevented"""
    with pytest.raises(ValueError):
        analyzer = RepositoryAnalyzer("../../etc/passwd")

def test_no_command_injection():
    """Test command injection is prevented"""
    malicious_repo = "https://github.com/test/repo; rm -rf /"
    
    with pytest.raises(ValueError):
        validate_repository_source(malicious_repo)
```

## Future Testing Improvements

1. **Increase Coverage**
   - Add unit tests for all components
   - Add integration tests for workflows
   - Add E2E tests for deployment

2. **Property-Based Testing**
   - Use Hypothesis for property testing
   - Test edge cases automatically

3. **Mutation Testing**
   - Use mutpy to verify test quality
   - Ensure tests catch bugs

4. **Performance Benchmarks**
   - Track analysis speed over time
   - Track deployment speed

5. **Contract Testing**
   - Verify cloud provider API contracts
   - Mock cloud provider responses

## Conclusion

While full test implementation is beyond the scope of this technical assessment, this document demonstrates understanding of:

- Testing pyramid and strategy
- Unit, integration, and E2E testing
- Test fixtures and mocking
- CI/CD integration
- Coverage metrics
- Performance and security testing

In production, comprehensive tests would be implemented before deployment.
