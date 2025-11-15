#!/usr/bin/env python3
"""
Setup tree-sitter language grammars.
"""

import subprocess
import sys
from pathlib import Path


def install_tree_sitter_languages():
    """Install tree-sitter language grammars."""
    languages = [
        'tree-sitter-python',
        'tree-sitter-cpp',
        'tree-sitter-c',
    ]
    
    print("Installing tree-sitter language grammars...")
    print("=" * 60)
    
    for lang in languages:
        print(f"\nInstalling {lang}...")
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', lang, '--break-system-packages'],
                check=True
            )
            print(f"✓ {lang} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {lang}: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("All language grammars installed successfully!")
    print("\nYou can now run:")
    print("  python scripts/review_mr.py <mr_file.json>")
    
    return True


def verify_installation():
    """Verify that tree-sitter languages are properly installed."""
    print("\nVerifying installation...")
    
    try:
        import tree_sitter
        import tree_sitter_python
        import tree_sitter_cpp
        import tree_sitter_c
        
        print("✓ All tree-sitter modules imported successfully")
        
        # Test creating parsers
        from tree_sitter import Language
        
        PY_LANGUAGE = Language(tree_sitter_python.language())
        CPP_LANGUAGE = Language(tree_sitter_cpp.language())
        C_LANGUAGE = Language(tree_sitter_c.language())
        
        py_parser = tree_sitter.Parser(PY_LANGUAGE)
        cpp_parser = tree_sitter.Parser(CPP_LANGUAGE)
        c_parser = tree_sitter.Parser(C_LANGUAGE)
        
        print("✓ All parsers created successfully")
        
        # Test parsing simple code
        test_code = b"def hello(): pass"
        tree = py_parser.parse(test_code)
        
        print("✓ Test parsing successful")
        print("\nSetup complete! ✨")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("\nPlease run the installation again.")
        return False
    except Exception as e:
        print(f"✗ Verification error: {e}")
        return False


if __name__ == '__main__':
    success = install_tree_sitter_languages()
    
    if success:
        verify_installation()
    else:
        sys.exit(1)
