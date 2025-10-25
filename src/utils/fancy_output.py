"""
Fancy terminal output utilities for modern UX
"""
import qrcode
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from io import StringIO
import time

console = Console()


def display_gradient_banner():
    """Display a fancy gradient banner"""
    banner_text = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║              🚀 AutoDeploy System v1.0                   ║
    ║                                                           ║
    ║     Automated Cloud Deployment from Natural Language     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    
    # Create gradient effect with rich
    gradient_banner = Text(banner_text)
    gradient_banner.stylize("bold cyan", 0, len(banner_text) // 3)
    gradient_banner.stylize("bold blue", len(banner_text) // 3, 2 * len(banner_text) // 3)
    gradient_banner.stylize("bold magenta", 2 * len(banner_text) // 3, len(banner_text))
    
    console.print(Panel(gradient_banner, border_style="bold blue", box=box.DOUBLE))


def display_qr_code(url: str):
    """Display a QR code for the deployed URL in terminal"""
    try:
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=1,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Get ASCII representation
        qr_ascii = StringIO()
        qr.print_ascii(out=qr_ascii, invert=True)
        qr_string = qr_ascii.getvalue()
        
        # Display with rich
        console.print("\n[bold cyan]📱 Scan to Access Your App:[/bold cyan]")
        console.print(Panel(
            qr_string,
            title="[bold]QR Code[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        ))
        console.print(f"[dim]Or visit: {url}[/dim]\n")
        
    except Exception as e:
        # Fallback if QR generation fails
        console.print(f"[dim]QR Code generation skipped: {e}[/dim]")


def celebrate_success(deployment_url: str, cloud_provider: str, deployment_time: float):
    """Display a celebration message with deployment summary"""
    
    # Create celebration
    console.print("\n" + "🎉 " * 20)
    console.print("\n[bold green]✨ DEPLOYMENT SUCCESSFUL! ✨[/bold green]\n", justify="center")
    
    # Create deployment summary table
    table = Table(
        title="[bold]Deployment Summary[/bold]",
        show_header=True,
        header_style="bold cyan",
        border_style="green",
        box=box.ROUNDED
    )
    
    table.add_column("Metric", style="cyan", width=25)
    table.add_column("Value", style="green", width=50)
    
    table.add_row("🌐 Deployment URL", f"[link={deployment_url}]{deployment_url}[/link]")
    table.add_row("☁️  Cloud Provider", cloud_provider.upper())
    table.add_row("⏱️  Deployment Time", f"{deployment_time:.1f} seconds")
    table.add_row("✅ Status", "[bold green]LIVE & RUNNING[/bold green]")
    
    console.print(table)
    
    # Display QR code
    display_qr_code(deployment_url)
    
    # Success message
    console.print(Panel(
        "[bold green]Your application is now live and accessible!\n"
        "Click the URL above or scan the QR code to access it.[/bold green]",
        border_style="green",
        box=box.DOUBLE
    ))


def display_live_progress(message: str, duration: float = 2.0):
    """Display a live progress spinner"""
    from rich.live import Live
    from rich.spinner import Spinner
    
    with Live(Spinner("dots", text=message), console=console) as live:
        time.sleep(duration)


def display_deployment_stages():
    """Display deployment pipeline stages"""
    stages = [
        ("🔍", "Repository Analysis", "cyan"),
        ("🧠", "NLP Processing", "blue"),
        ("🏗️", "Infrastructure Planning", "magenta"),
        ("⚙️", "Terraform Generation", "yellow"),
        ("🚀", "Cloud Deployment", "green"),
        ("🔧", "Application Setup", "cyan"),
        ("✅", "Verification", "green"),
    ]
    
    table = Table(
        title="[bold]Deployment Pipeline[/bold]",
        show_header=False,
        border_style="cyan",
        box=box.MINIMAL
    )
    
    table.add_column("Stage", width=3)
    table.add_column("Description", width=30)
    
    for emoji, stage, color in stages:
        table.add_row(emoji, f"[{color}]{stage}[/{color}]")
    
    console.print(table)


def display_clickable_link(url: str, text: str = "Open Deployment"):
    """Display a clickable terminal link"""
    # Rich automatically makes URLs clickable
    console.print(f"\n🔗 [bold cyan][link={url}]{text}[/link][/bold cyan]")
    console.print(f"   {url}\n")


def display_tech_stack(analysis: dict):
    """Display detected tech stack in a fancy table"""
    table = Table(
        title="[bold cyan]🔍 Detected Tech Stack[/bold cyan]",
        show_header=True,
        header_style="bold yellow",
        border_style="cyan",
        box=box.ROUNDED
    )
    
    table.add_column("Component", style="cyan", width=20)
    table.add_column("Details", style="white", width=40)
    
    # Map analysis to readable format
    tech_items = [
        ("Language", analysis.get('language', 'Unknown')),
        ("Framework", analysis.get('framework', 'Unknown')),
        ("App Type", analysis.get('app_type', 'Unknown')),
        ("Port", str(analysis.get('port', 'N/A'))),
        ("Database", "Yes" if analysis.get('requires_database') else "No"),
        ("Confidence", f"{int(analysis.get('confidence_score', 0) * 100)}%"),
    ]
    
    for component, detail in tech_items:
        # Add emoji based on component
        emoji = {
            "Language": "💻",
            "Framework": "🛠️",
            "App Type": "📦",
            "Port": "🔌",
            "Database": "🗄️",
            "Confidence": "🎯"
        }.get(component, "•")
        
        table.add_row(f"{emoji} {component}", detail)
    
    console.print(table)


def display_cost_estimate(cost: float, cloud: str):
    """Display monthly cost estimate"""
    console.print(Panel(
        f"[bold yellow]💰 Estimated Monthly Cost[/bold yellow]\n\n"
        f"Cloud Provider: [cyan]{cloud.upper()}[/cyan]\n"
        f"Estimated Cost: [green]${cost:.2f}/month[/green]\n\n"
        f"[dim]* Based on current configuration\n"
        f"* Actual costs may vary based on usage[/dim]",
        border_style="yellow",
        box=box.ROUNDED
    ))


def display_next_steps(deployment_url: str):
    """Display suggested next steps"""
    steps = [
        "✅ Access your application at the URL above",
        "📊 Monitor logs: Check cloud provider console",
        "🔒 Configure SSL: Add custom domain and certificate",
        "📈 Scale up: Modify Terraform for auto-scaling",
        "🔐 Secure: Review security groups and access policies",
    ]
    
    console.print("\n[bold cyan]📋 Next Steps:[/bold cyan]")
    for step in steps:
        console.print(f"  {step}")
    console.print()
