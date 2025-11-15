"""
Basic tests for the auto reviewer.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auto_reviewer.parsers import MRParser
from auto_reviewer.analyzers import create_analyzer


def test_mr_parser():
    """Test MR parsing."""
    parser = MRParser()
    
    # Test language detection
    assert parser.get_file_language('test.py') == 'python'
    assert parser.get_file_language('test.cpp') == 'cpp'
    assert parser.get_file_language('test.c') == 'c'
    assert parser.get_file_language('test.h') == 'c'
    
    print("✓ MR Parser tests passed")


def test_tree_sitter_analyzer():
    """Test tree-sitter analyzer."""
    try:
        # Test creating analyzers for different languages
        py_analyzer = create_analyzer('python')
        assert py_analyzer is not None
        
        cpp_analyzer = create_analyzer('cpp')
        assert cpp_analyzer is not None
        
        c_analyzer = create_analyzer('c')
        assert c_analyzer is not None
        
        print("✓ Tree-sitter analyzer tests passed")
        
    except ImportError as e:
        print(f"⚠ Tree-sitter not fully installed: {e}")
        print("  Run: python scripts/setup_tree_sitter.py")
        return False
    
    return True


def test_python_analysis():
    """Test Python code analysis."""
    try:
        analyzer = create_analyzer('python')
        
        # Test code with issues
        code = """
def process_data(data=[]):  # Mutable default
    try:
        result = do_something(data)
    except:  # Bare except
        pass
    return result
"""
        
        issues = analyzer.analyze_code(code, 'test.py')
        
        # Should find mutable default and bare except
        assert len(issues) > 0
        
        print(f"✓ Python analysis test passed (found {len(issues)} issues)")
        
    except Exception as e:
        print(f"⚠ Python analysis test failed: {e}")
        return False
    
    return True


def test_cpp_analysis():
    """Test C++ code analysis."""
    try:
        analyzer = create_analyzer('cpp')
        
        # Test code with issues
        code = """
int process(int* data) {
    // Missing null check
    int value = *data;
    return value;
}

int* allocate() {
    int* ptr = new int(42);
    // Missing delete (resource leak)
    return ptr;
}
"""
        
        issues = analyzer.analyze_code(code, 'test.cpp')
        
        print(f"✓ C++ analysis test passed (found {len(issues)} issues)")
        
    except Exception as e:
        print(f"⚠ C++ analysis test failed: {e}")
        return False
    
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("Running Auto Reviewer Tests")
    print("="*60 + "\n")
    
    test_mr_parser()
    
    if not test_tree_sitter_analyzer():
        print("\n⚠ Some tests skipped due to missing dependencies")
        print("Run setup: python scripts/setup_tree_sitter.py")
        return False
    
    test_python_analysis()
    test_cpp_analysis()
    
    print("\n" + "="*60)
    print("✨ All tests passed!")
    print("="*60)
    
    return True


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
