#!/usr/bin/env python3
"""
AutoDeploy - Automated Application Deployment System
Main CLI Entry Point
"""
import os
import sys
import click
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.analyzer.repo_analyzer import RepositoryAnalyzer
from src.nlp.requirement_parser import RequirementParser
from src.infrastructure.decision_engine import InfrastructureDecisionEngine
from src.infrastructure.terraform_generator import TerraformGenerator
from src.deployer.orchestrator import DeploymentOrchestrator
from src.utils.logger import setup_logger
from src.utils.validators import (
    validate_repository_source,
    validate_deployment_description
)
from src.utils.fancy_output import display_gradient_banner, display_tech_stack

# Load environment variables
load_dotenv()

console = Console()
logger = setup_logger('autodeploy')


def display_banner():
    """Display fancy application banner with gradient"""
    try:
        # Use fancy gradient banner
        display_gradient_banner()
    except Exception:
        # Fallback to simple banner
        banner = """
        ╔═══════════════════════════════════════════════════════════╗
        ║                                                           ║
        ║              🚀 AutoDeploy System v1.0                   ║
        ║                                                           ║
        ║     Automated Cloud Deployment from Natural Language     ║
        ║                                                           ║
        ╚═══════════════════════════════════════════════════════════╝
        """
        console.print(Panel(banner, style="bold blue"))


@click.group()
def cli():
    """AutoDeploy - Automated application deployment system"""
    pass


@cli.command()
@click.option('--repo', '-r', required=True, help='GitHub URL, local path, or zip file')
@click.option('--description', '-d', required=True, help='Natural language deployment description')
@click.option('--dry-run', is_flag=True, help='Analyze without deploying')
@click.option('--output-dir', '-o', help='Output directory for generated files')
def deploy(repo: str, description: str, dry_run: bool, output_dir: str):
    """Deploy an application to the cloud"""
    
    display_banner()
    
    # Validate inputs
    if not validate_repository_source(repo):
        console.print("[red]Error: Invalid repository source[/red]")
        console.print(f"Provided: {repo}")
        console.print("Must be a valid URL, local directory path, or zip file")
        sys.exit(1)
    
    if not validate_deployment_description(description):
        console.print("[red]Error: Deployment description too short[/red]")
        console.print("Please provide a detailed description (at least 10 characters)")
        sys.exit(1)
    
    console.print("\n[bold cyan]📋 Deployment Request[/bold cyan]")
    console.print(f"Repository: {repo}")
    console.print(f"Description: {description}")
    console.print(f"Mode: {'Dry Run (Analysis Only)' if dry_run else 'Full Deployment'}\n")
    
    try:
        # Step 1: Analyze Repository
        console.print("[bold yellow]Step 1/6:[/bold yellow] Analyzing repository...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Cloning and analyzing repository...", total=None)
            
            # Clone/prepare repo for analysis
            import tempfile
            import shutil
            from git import Repo as GitRepo
            
            temp_dir = Path(tempfile.mkdtemp())
            
            if repo.startswith(('http://', 'https://', 'git@')):
                GitRepo.clone_from(repo, temp_dir)
            elif os.path.isdir(repo):
                shutil.copytree(repo, temp_dir, dirs_exist_ok=True)
            else:
                console.print("[red]Unsupported repository source[/red]")
                sys.exit(1)
            
            analyzer = RepositoryAnalyzer(str(temp_dir))
            app_analysis = analyzer.analyze()
            
            progress.update(task, completed=True)
        
        console.print("[green]✓[/green] Repository analyzed successfully\n")
        
        # Display analysis results
        _display_analysis(app_analysis)
        
        # Step 2: Parse Deployment Requirements
        console.print("\n[bold yellow]Step 2/6:[/bold yellow] Parsing deployment requirements...")
        
        parser = RequirementParser()
        requirements = parser.parse(description, app_analysis.to_dict())
        
        console.print("[green]✓[/green] Requirements parsed successfully\n")
        _display_requirements(requirements)
        
        # Step 3: Make Infrastructure Decisions
        console.print("\n[bold yellow]Step 3/6:[/bold yellow] Determining infrastructure strategy...")
        
        decision_engine = InfrastructureDecisionEngine()
        infrastructure = decision_engine.decide(
            app_analysis.to_dict(),
            requirements.to_dict()
        )
        
        console.print("[green]✓[/green] Infrastructure strategy determined\n")
        _display_infrastructure(infrastructure)
        
        if dry_run:
            console.print("\n[bold cyan]Dry run completed. No deployment performed.[/bold cyan]")
            
            # Save analysis to file
            if output_dir:
                _save_analysis(output_dir, app_analysis, requirements, infrastructure)
            
            return
        
        # Confirm deployment
        console.print(f"\n[bold yellow]Estimated Cost:[/bold yellow] {infrastructure.estimated_cost}")
        
        if not Confirm.ask("\n[bold]Proceed with deployment?[/bold]", default=False):
            console.print("[yellow]Deployment cancelled by user[/yellow]")
            return
        
        # Step 4: Generate Terraform Configuration
        console.print("\n[bold yellow]Step 4/6:[/bold yellow] Generating infrastructure code...")
        
        tf_dir = output_dir or str(Path.cwd() / 'deployments' / 'terraform')
        generator = TerraformGenerator(tf_dir)
        generator.generate(infrastructure.to_dict(), app_analysis.to_dict())
        
        console.print(f"[green]✓[/green] Terraform configuration generated at {tf_dir}\n")
        
        # Step 5 & 6: Deploy
        console.print("[bold yellow]Step 5/6:[/bold yellow] Provisioning infrastructure...")
        console.print("[bold yellow]Step 6/6:[/bold yellow] Deploying application...\n")
        
        orchestrator = DeploymentOrchestrator(work_dir=output_dir)
        result = orchestrator.deploy(
            repo_source=repo,
            app_analysis=app_analysis.to_dict(),
            infrastructure=infrastructure.to_dict(),
            requirements=requirements.to_dict()
        )
        
        if result['status'] == 'success':
            console.print("\n[bold green]🎉 Deployment completed successfully![/bold green]")
            
            # Save deployment info
            if output_dir:
                _save_deployment_info(output_dir, result)
        else:
            console.print(f"\n[bold red]❌ Deployment failed: {result.get('error')}[/bold red]")
            sys.exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Deployment cancelled by user[/yellow]")
        sys.exit(0)
    
    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")
        logger.exception("Deployment failed")
        sys.exit(1)


@cli.command()
@click.argument('repo')
def analyze(repo: str):
    """Analyze a repository without deploying"""
    
    display_banner()
    
    console.print(f"\n[bold cyan]Analyzing repository:[/bold cyan] {repo}\n")
    
    try:
        import tempfile
        import shutil
        from git import Repo as GitRepo
        
        temp_dir = Path(tempfile.mkdtemp())
        
        if repo.startswith(('http://', 'https://', 'git@')):
            console.print("Cloning repository...")
            GitRepo.clone_from(repo, temp_dir)
        elif os.path.isdir(repo):
            shutil.copytree(repo, temp_dir, dirs_exist_ok=True)
        else:
            console.print("[red]Invalid repository source[/red]")
            sys.exit(1)
        
        analyzer = RepositoryAnalyzer(str(temp_dir))
        app_analysis = analyzer.analyze()
        
        _display_analysis(app_analysis)
        
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)


def _display_analysis(analysis):
    """Display repository analysis results"""
    from rich.table import Table
    
    table = Table(title="Repository Analysis", show_header=True)
    table.add_column("Property", style="cyan", width=25)
    table.add_column("Value", style="green")
    
    table.add_row("Application Type", analysis.app_type)
    table.add_row("Framework", analysis.framework or "N/A")
    table.add_row("Language", analysis.language)
    table.add_row("Entry Point", analysis.entry_point or "N/A")
    table.add_row("Start Command", analysis.start_command or "N/A")
    table.add_row("Port", str(analysis.port))
    table.add_row("Requires Database", "Yes" if analysis.requires_database else "No")
    
    if analysis.requires_database:
        table.add_row("Database Type", analysis.database_type or "N/A")
    
    table.add_row("Requires Redis", "Yes" if analysis.requires_redis else "No")
    table.add_row("Has Dockerfile", "Yes" if analysis.dockerfile_present else "No")
    table.add_row("Confidence Score", f"{analysis.confidence_score:.0%}")
    
    console.print(table)
    
    # Display dependencies
    if analysis.dependencies:
        console.print("\n[bold]Dependencies:[/bold]")
        for lang, deps in analysis.dependencies.items():
            console.print(f"  {lang}: {len(deps)} packages")


def _display_requirements(requirements):
    """Display parsed deployment requirements"""
    from rich.table import Table
    
    table = Table(title="Deployment Requirements", show_header=True)
    table.add_column("Property", style="cyan", width=25)
    table.add_column("Value", style="green")
    
    table.add_row("Cloud Provider", requirements.cloud_provider.upper())
    table.add_row("Deployment Type", requirements.deployment_type.title())
    table.add_row("Region", requirements.region or "Default")
    table.add_row("Instance Type", requirements.instance_type or "Auto")
    table.add_row("Auto Scaling", "Yes" if requirements.scaling.get('auto') else "No")
    table.add_row("SSL Required", "Yes" if requirements.ssl_required else "No")
    
    if requirements.custom_domain:
        table.add_row("Custom Domain", requirements.custom_domain)
    
    if requirements.additional_services:
        table.add_row("Additional Services", ", ".join(requirements.additional_services))
    
    console.print(table)


def _display_infrastructure(infrastructure):
    """Display infrastructure decisions"""
    from rich.table import Table
    
    table = Table(title="Infrastructure Strategy", show_header=True)
    table.add_column("Component", style="cyan", width=25)
    table.add_column("Configuration", style="green")
    
    compute = infrastructure.compute_resources
    table.add_row("Deployment Strategy", infrastructure.deployment_strategy.title())
    table.add_row("Compute Type", compute.get('type', 'N/A'))
    
    if compute.get('instance_type'):
        table.add_row("Instance Type", compute['instance_type'])
    
    table.add_row("Instance Count", f"{compute.get('count', 1)} (min) - {compute.get('max_count', 1)} (max)")
    
    if infrastructure.database.get('required'):
        db = infrastructure.database
        table.add_row("Database", f"{db['type']} ({db['instance_class']})")
    
    table.add_row("Estimated Cost", infrastructure.estimated_cost)
    
    console.print(table)
    console.print(f"\n[italic]{infrastructure.reasoning}[/italic]")


def _save_analysis(output_dir: str, analysis, requirements, infrastructure):
    """Save analysis results to file"""
    import json
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    data = {
        'analysis': analysis.to_dict(),
        'requirements': requirements.to_dict(),
        'infrastructure': infrastructure.to_dict(),
    }
    
    with open(output_path / 'analysis.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    console.print(f"\n[green]Analysis saved to {output_path / 'analysis.json'}[/green]")


def _save_deployment_info(output_dir: str, result: dict):
    """Save deployment information"""
    import json
    from datetime import datetime
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    result['timestamp'] = datetime.now().isoformat()
    
    with open(output_path / 'deployment.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    console.print(f"[green]Deployment info saved to {output_path / 'deployment.json'}[/green]")


if __name__ == '__main__':
    cli()
