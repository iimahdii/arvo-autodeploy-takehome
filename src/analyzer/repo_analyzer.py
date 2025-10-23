"""
Repository Analyzer - Detects application type, dependencies, and deployment requirements
"""
import os
import json
import toml
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import re


@dataclass
class AnalysisResult:
    """Container for repository analysis results"""
    app_type: str  # flask, django, node, react, etc.
    framework: Optional[str]
    language: str
    dependencies: Dict[str, List[str]]
    entry_point: Optional[str]
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
    confidence_score: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


class RepositoryAnalyzer:
    """Analyzes a code repository to determine deployment requirements"""
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'flask': ['from flask import', 'Flask(__name__)', 'requirements.txt'],
        'django': ['django', 'manage.py', 'settings.py', 'wsgi.py'],
        'fastapi': ['from fastapi import', 'FastAPI()', 'uvicorn'],
        'express': ['express', 'app.listen', 'package.json'],
        'nextjs': ['next.config', 'pages/', 'package.json'],
        'react': ['react', 'react-dom', 'package.json', 'src/App'],
        'vue': ['vue', 'package.json', 'src/main'],
        'angular': ['@angular', 'angular.json', 'package.json'],
        'rails': ['Gemfile', 'config.ru', 'app/controllers'],
        'laravel': ['composer.json', 'artisan', 'app/Http'],
        'spring': ['pom.xml', 'build.gradle', 'src/main/java'],
    }
    
    # Database detection patterns
    DATABASE_PATTERNS = {
        'postgresql': ['psycopg2', 'pg', 'postgres', 'postgresql'],
        'mysql': ['mysql', 'pymysql', 'mysql2'],
        'mongodb': ['pymongo', 'mongoose', 'mongodb'],
        'redis': ['redis', 'redis-py', 'ioredis'],
        'sqlite': ['sqlite3', 'sqlite'],
    }
    
    # Port defaults by framework
    DEFAULT_PORTS = {
        'flask': 5000,
        'django': 8000,
        'fastapi': 8000,
        'express': 3000,
        'nextjs': 3000,
        'react': 3000,
        'vue': 8080,
        'angular': 4200,
        'rails': 3000,
        'laravel': 8000,
        'spring': 8080,
    }
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.files = self._scan_files()
        
    def _scan_files(self) -> Set[str]:
        """Recursively scan all files in repository"""
        files = set()
        for root, _, filenames in os.walk(self.repo_path):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), self.repo_path)
                files.add(rel_path)
        return files
    
    def analyze(self) -> AnalysisResult:
        """Perform comprehensive repository analysis"""
        
        # Detect language
        language = self._detect_language()
        
        # Detect framework and app type
        app_type, framework = self._detect_framework()
        
        # Parse dependencies
        dependencies = self._parse_dependencies()
        
        # Detect database requirements
        requires_db, db_type = self._detect_database(dependencies)
        
        # Detect Redis
        requires_redis = self._detect_redis(dependencies)
        
        # Find entry point and commands
        entry_point = self._find_entry_point(app_type, framework)
        build_command = self._determine_build_command(app_type, framework)
        start_command = self._determine_start_command(app_type, framework, entry_point)
        
        # Detect port
        port = self._detect_port(app_type, framework)
        
        # Find environment variables
        env_vars = self._find_environment_variables()
        
        # Check Docker files
        dockerfile_present = 'Dockerfile' in self.files
        docker_compose_present = any(f in self.files for f in ['docker-compose.yml', 'docker-compose.yaml'])
        
        # Check for static files
        static_files = self._has_static_files()
        
        # Calculate confidence score
        confidence = self._calculate_confidence(app_type, framework, entry_point)
        
        return AnalysisResult(
            app_type=app_type,
            framework=framework,
            language=language,
            dependencies=dependencies,
            entry_point=entry_point,
            build_command=build_command,
            start_command=start_command,
            port=port,
            environment_vars=env_vars,
            requires_database=requires_db,
            database_type=db_type,
            requires_redis=requires_redis,
            requires_docker=dockerfile_present or docker_compose_present,
            dockerfile_present=dockerfile_present,
            docker_compose_present=docker_compose_present,
            static_files=static_files,
            confidence_score=confidence
        )
    
    def _detect_language(self) -> str:
        """Detect primary programming language"""
        extensions = {'.py': 0, '.js': 0, '.ts': 0, '.java': 0, '.rb': 0, '.php': 0, '.go': 0}
        
        for file in self.files:
            ext = Path(file).suffix
            if ext in extensions:
                extensions[ext] += 1
        
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.rb': 'ruby',
            '.php': 'php',
            '.go': 'go'
        }
        
        if extensions:
            dominant_ext = max(extensions, key=extensions.get)
            return lang_map.get(dominant_ext, 'unknown')
        
        return 'unknown'
    
    def _detect_framework(self) -> tuple[str, Optional[str]]:
        """Detect application framework"""
        scores = {fw: 0 for fw in self.FRAMEWORK_PATTERNS}
        
        # Check file existence
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for pattern in patterns:
                if any(pattern.lower() in f.lower() for f in self.files):
                    scores[framework] += 1
        
        # Check file contents for imports
        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            for file in self.files:
                if file.endswith(('.py', '.js', '.ts', '.rb', '.php')):
                    try:
                        content = (self.repo_path / file).read_text(errors='ignore')
                        for pattern in patterns:
                            if pattern in content:
                                scores[framework] += 2
                    except:
                        pass
        
        if scores:
            detected = max(scores, key=scores.get)
            if scores[detected] > 0:
                return detected, detected
        
        return 'generic', None
    
    def _parse_dependencies(self) -> Dict[str, List[str]]:
        """Parse dependency files"""
        deps = {}
        
        # Python - requirements.txt
        if 'requirements.txt' in self.files:
            try:
                content = (self.repo_path / 'requirements.txt').read_text()
                deps['python'] = [line.split('==')[0].split('>=')[0].strip() 
                                 for line in content.split('\n') 
                                 if line.strip() and not line.startswith('#')]
            except:
                pass
        
        # Python - Pipfile
        if 'Pipfile' in self.files:
            try:
                content = toml.load(self.repo_path / 'Pipfile')
                deps['python'] = list(content.get('packages', {}).keys())
            except:
                pass
        
        # Node - package.json
        if 'package.json' in self.files:
            try:
                content = json.loads((self.repo_path / 'package.json').read_text())
                deps['node'] = list(content.get('dependencies', {}).keys())
                deps['node_dev'] = list(content.get('devDependencies', {}).keys())
            except:
                pass
        
        # Ruby - Gemfile
        if 'Gemfile' in self.files:
            try:
                content = (self.repo_path / 'Gemfile').read_text()
                gems = re.findall(r"gem\s+['\"]([^'\"]+)['\"]", content)
                deps['ruby'] = gems
            except:
                pass
        
        # PHP - composer.json
        if 'composer.json' in self.files:
            try:
                content = json.loads((self.repo_path / 'composer.json').read_text())
                deps['php'] = list(content.get('require', {}).keys())
            except:
                pass
        
        return deps
    
    def _detect_database(self, dependencies: Dict[str, List[str]]) -> tuple[bool, Optional[str]]:
        """Detect if database is required and which type"""
        all_deps = []
        for dep_list in dependencies.values():
            all_deps.extend([d.lower() for d in dep_list])
        
        for db_type, patterns in self.DATABASE_PATTERNS.items():
            if db_type == 'redis':  # Skip redis, handled separately
                continue
            for pattern in patterns:
                if any(pattern in dep for dep in all_deps):
                    return True, db_type
        
        # Check for database keywords in files
        db_keywords = ['database', 'db_', 'DATABASE_URL', 'DB_HOST']
        for file in self.files:
            if file.endswith(('.py', '.js', '.env', '.yml', '.yaml')):
                try:
                    content = (self.repo_path / file).read_text(errors='ignore')
                    if any(kw in content for kw in db_keywords):
                        return True, 'postgresql'  # Default to postgres
                except:
                    pass
        
        return False, None
    
    def _detect_redis(self, dependencies: Dict[str, List[str]]) -> bool:
        """Detect if Redis is required"""
        all_deps = []
        for dep_list in dependencies.values():
            all_deps.extend([d.lower() for d in dep_list])
        
        redis_patterns = self.DATABASE_PATTERNS['redis']
        return any(pattern in dep for pattern in redis_patterns for dep in all_deps)
    
    def _find_entry_point(self, app_type: str, framework: Optional[str]) -> Optional[str]:
        """Find application entry point"""
        entry_points = {
            'flask': ['app.py', 'main.py', 'wsgi.py', 'application.py'],
            'django': ['manage.py'],
            'fastapi': ['main.py', 'app.py'],
            'express': ['index.js', 'server.js', 'app.js', 'main.js'],
            'nextjs': ['package.json'],
            'react': ['package.json'],
            'rails': ['config.ru'],
            'laravel': ['artisan'],
        }
        
        candidates = entry_points.get(framework or app_type, ['main.py', 'app.py', 'index.js'])
        
        for candidate in candidates:
            if candidate in self.files:
                return candidate
        
        return None
    
    def _determine_build_command(self, app_type: str, framework: Optional[str]) -> Optional[str]:
        """Determine build command"""
        build_commands = {
            'nextjs': 'npm run build',
            'react': 'npm run build',
            'vue': 'npm run build',
            'angular': 'ng build',
        }
        
        return build_commands.get(framework or app_type)
    
    def _determine_start_command(self, app_type: str, framework: Optional[str], 
                                 entry_point: Optional[str]) -> Optional[str]:
        """Determine start command"""
        if framework == 'flask' and entry_point:
            return f"python {entry_point}"
        elif framework == 'django':
            return "python manage.py runserver 0.0.0.0:8000"
        elif framework == 'fastapi' and entry_point:
            app_name = entry_point.replace('.py', '')
            return f"uvicorn {app_name}:app --host 0.0.0.0 --port 8000"
        elif framework in ['express', 'nextjs', 'react']:
            # Check package.json for start script
            if 'package.json' in self.files:
                try:
                    pkg = json.loads((self.repo_path / 'package.json').read_text())
                    if 'scripts' in pkg and 'start' in pkg['scripts']:
                        return 'npm start'
                except:
                    pass
            return 'node index.js' if entry_point else 'npm start'
        elif framework == 'rails':
            return 'rails server -b 0.0.0.0'
        elif framework == 'laravel':
            return 'php artisan serve --host=0.0.0.0'
        
        return None
    
    def _detect_port(self, app_type: str, framework: Optional[str]) -> int:
        """Detect application port"""
        # Check common config files
        for file in self.files:
            if file.endswith(('.env', '.env.example', 'config.py', 'settings.py')):
                try:
                    content = (self.repo_path / file).read_text(errors='ignore')
                    port_match = re.search(r'PORT[=:\s]+(\d+)', content, re.IGNORECASE)
                    if port_match:
                        return int(port_match.group(1))
                except:
                    pass
        
        # Return default port for framework
        return self.DEFAULT_PORTS.get(framework or app_type, 8000)
    
    def _find_environment_variables(self) -> List[str]:
        """Find required environment variables"""
        env_vars = set()
        
        # Check .env.example files
        for file in ['.env.example', '.env.sample', 'env.example']:
            if file in self.files:
                try:
                    content = (self.repo_path / file).read_text()
                    for line in content.split('\n'):
                        if '=' in line and not line.strip().startswith('#'):
                            var_name = line.split('=')[0].strip()
                            env_vars.add(var_name)
                except:
                    pass
        
        # Common patterns in code
        for file in self.files:
            if file.endswith(('.py', '.js', '.ts')):
                try:
                    content = (self.repo_path / file).read_text(errors='ignore')
                    # Python: os.environ.get('VAR') or os.getenv('VAR')
                    env_vars.update(re.findall(r"os\.(?:environ\.get|getenv)\(['\"]([^'\"]+)['\"]", content))
                    # Node: process.env.VAR
                    env_vars.update(re.findall(r"process\.env\.([A-Z_][A-Z0-9_]*)", content))
                except:
                    pass
        
        return sorted(list(env_vars))
    
    def _has_static_files(self) -> bool:
        """Check if application has static files"""
        static_dirs = ['static', 'public', 'assets', 'dist', 'build']
        return any(any(d in f for d in static_dirs) for f in self.files)
    
    def _calculate_confidence(self, app_type: str, framework: Optional[str], 
                             entry_point: Optional[str]) -> float:
        """Calculate confidence score for analysis"""
        score = 0.0
        
        if app_type != 'generic':
            score += 0.3
        
        if framework:
            score += 0.3
        
        if entry_point:
            score += 0.2
        
        if any(f in self.files for f in ['requirements.txt', 'package.json', 'Gemfile']):
            score += 0.2
        
        return min(score, 1.0)
