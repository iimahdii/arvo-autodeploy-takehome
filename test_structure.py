#!/usr/bin/env python3
"""
Test script to verify project structure and imports
Run this before installing dependencies to check structure
"""
import os
import sys
from pathlib import Path

def test_structure():
    """Test that all required files and directories exist"""
    
    print("🧪 Testing AutoDeploy Project Structure\n")
    
    required_files = [
        'main.py',
        'requirements.txt',
        '.env.example',
        '.gitignore',
        'README.md',
        'ARCHITECTURE.md',
        'DEMO.md',
        'setup.sh',
        'src/__init__.py',
        'src/analyzer/__init__.py',
        'src/analyzer/repo_analyzer.py',
        'src/nlp/__init__.py',
        'src/nlp/requirement_parser.py',
        'src/infrastructure/__init__.py',
        'src/infrastructure/decision_engine.py',
        'src/infrastructure/terraform_generator.py',
        'src/deployer/__init__.py',
        'src/deployer/orchestrator.py',
        'src/utils/__init__.py',
        'src/utils/logger.py',
        'src/utils/validators.py',
    ]
    
    required_dirs = [
        'src',
        'src/analyzer',
        'src/nlp',
        'src/infrastructure',
        'src/deployer',
        'src/utils',
    ]
    
    print("Checking directories...")
    all_dirs_exist = True
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - MISSING")
            all_dirs_exist = False
    
    print("\nChecking files...")
    all_files_exist = True
    for file_path in required_files:
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {file_path} ({size} bytes)")
        else:
            print(f"  ✗ {file_path} - MISSING")
            all_files_exist = False
    
    print("\nChecking Python syntax...")
    python_files = [
        'main.py',
        'src/analyzer/repo_analyzer.py',
        'src/nlp/requirement_parser.py',
        'src/infrastructure/decision_engine.py',
        'src/infrastructure/terraform_generator.py',
        'src/deployer/orchestrator.py',
        'src/utils/logger.py',
        'src/utils/validators.py',
    ]
    
    syntax_ok = True
    for py_file in python_files:
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), py_file, 'exec')
            print(f"  ✓ {py_file}")
        except SyntaxError as e:
            print(f"  ✗ {py_file} - SYNTAX ERROR: {e}")
            syntax_ok = False
    
    print("\n" + "="*60)
    if all_dirs_exist and all_files_exist and syntax_ok:
        print("✅ All structure tests passed!")
        print("\nNext steps:")
        print("1. Run: ./setup.sh")
        print("2. Activate venv: source venv/bin/activate")
        print("3. Test CLI: python main.py --help")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(test_structure())
