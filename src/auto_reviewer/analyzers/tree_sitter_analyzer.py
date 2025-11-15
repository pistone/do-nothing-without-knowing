"""
Tree-sitter based code analyzer for structural analysis.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path
import tree_sitter


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    severity: str  # 'error', 'warning', 'info'
    category: str  # e.g., 'complexity', 'style', 'potential_bug'
    rule_id: str
    message: str
    file_path: str
    line_number: int
    column: int
    end_line: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None


class TreeSitterAnalyzer:
    """
    Analyzer using tree-sitter for structural code analysis.
    """
    
    def __init__(self, language: str):
        """
        Initialize analyzer for a specific language.
        
        Args:
            language: Programming language ('c', 'cpp', 'python', etc.)
        """
        self.language = language
        self.parser = self._create_parser(language)
        self.rules = []  # Will be populated by rule classes
    
    def _create_parser(self, language: str):
        """Create a tree-sitter parser for the given language."""
        try:
            if language == 'python':
                from tree_sitter import Language
                import tree_sitter_python
                PY_LANGUAGE = Language(tree_sitter_python.language())
                parser = tree_sitter.Parser(PY_LANGUAGE)
                return parser
            elif language == 'cpp' or language == 'c':
                from tree_sitter import Language
                import tree_sitter_cpp
                CPP_LANGUAGE = Language(tree_sitter_cpp.language())
                parser = tree_sitter.Parser(CPP_LANGUAGE)
                return parser
            elif language == 'c':
                from tree_sitter import Language
                import tree_sitter_c
                C_LANGUAGE = Language(tree_sitter_c.language())
                parser = tree_sitter.Parser(C_LANGUAGE)
                return parser
            else:
                raise ValueError(f"Unsupported language: {language}")
        except ImportError as e:
            raise ImportError(f"Tree-sitter language module not found for {language}: {e}")
    
    def analyze_code(self, code: str, file_path: str) -> List[CodeIssue]:
        """
        Analyze code and return found issues.
        
        Args:
            code: Source code as string
            file_path: Path to the file being analyzed
            
        Returns:
            List of CodeIssue objects
        """
        if not code or not code.strip():
            return []
        
        tree = self.parser.parse(bytes(code, 'utf8'))
        root = tree.root_node
        
        issues = []
        
        # Run all registered rules
        for rule in self.rules:
            rule_issues = rule.check(root, code, file_path)
            issues.extend(rule_issues)
        
        return issues
    
    def add_rule(self, rule):
        """Add a rule to the analyzer."""
        self.rules.append(rule)
    
    def query(self, node, query_string: str) -> List:
        """
        Execute a tree-sitter query.
        
        Args:
            node: Tree-sitter node to query
            query_string: Tree-sitter query string
            
        Returns:
            List of matches
        """
        # This is a simplified version - actual implementation would use tree_sitter.Query
        # For now, we'll use manual traversal
        return []


class AnalysisRule:
    """Base class for analysis rules."""
    
    def __init__(self, rule_id: str, severity: str, category: str):
        self.rule_id = rule_id
        self.severity = severity
        self.category = category
    
    def check(self, root_node, code: str, file_path: str) -> List[CodeIssue]:
        """
        Check the rule against the code.
        
        Args:
            root_node: Root node of the syntax tree
            code: Source code
            file_path: File path
            
        Returns:
            List of issues found
        """
        raise NotImplementedError("Subclasses must implement check()")
    
    def create_issue(self, message: str, node, file_path: str, 
                    suggestion: Optional[str] = None) -> CodeIssue:
        """Helper to create a CodeIssue from a node."""
        return CodeIssue(
            severity=self.severity,
            category=self.category,
            rule_id=self.rule_id,
            message=message,
            file_path=file_path,
            line_number=node.start_point[0] + 1,
            column=node.start_point[1],
            end_line=node.end_point[0] + 1,
            suggestion=suggestion
        )


class FunctionLengthRule(AnalysisRule):
    """Rule to check function length."""
    
    def __init__(self, max_length: int = 50, language: str = 'cpp'):
        super().__init__(
            rule_id='FUNC_TOO_LONG',
            severity='warning',
            category='complexity'
        )
        self.max_length = max_length
        self.language = language
    
    def check(self, root_node, code: str, file_path: str) -> List[CodeIssue]:
        issues = []
        
        # Find all function definitions
        functions = self._find_functions(root_node)
        
        for func_node in functions:
            func_length = func_node.end_point[0] - func_node.start_point[0] + 1
            
            if func_length > self.max_length:
                func_name = self._get_function_name(func_node)
                message = (f"Function '{func_name}' is {func_length} lines long, "
                          f"exceeds maximum of {self.max_length} lines")
                suggestion = "Consider breaking this function into smaller, more focused functions"
                
                issues.append(self.create_issue(message, func_node, file_path, suggestion))
        
        return issues
    
    def _find_functions(self, node):
        """Find all function definitions in the tree."""
        functions = []
        
        if self.language in ['c', 'cpp']:
            if node.type == 'function_definition':
                functions.append(node)
        elif self.language == 'python':
            if node.type == 'function_definition':
                functions.append(node)
        
        # Recursively search children
        for child in node.children:
            functions.extend(self._find_functions(child))
        
        return functions
    
    def _get_function_name(self, func_node) -> str:
        """Extract function name from function node."""
        for child in func_node.children:
            if child.type == 'identifier' or child.type == 'function_declarator':
                if child.type == 'identifier':
                    return child.text.decode('utf8')
                # For C/C++, the declarator contains the name
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        return subchild.text.decode('utf8')
        return '<unknown>'


class ComplexityRule(AnalysisRule):
    """Rule to check cyclomatic complexity (approximate via nesting)."""
    
    def __init__(self, max_complexity: int = 10, language: str = 'cpp'):
        super().__init__(
            rule_id='HIGH_COMPLEXITY',
            severity='warning',
            category='complexity'
        )
        self.max_complexity = max_complexity
        self.language = language
    
    def check(self, root_node, code: str, file_path: str) -> List[CodeIssue]:
        issues = []
        
        functions = self._find_functions(root_node)
        
        for func_node in functions:
            complexity = self._calculate_complexity(func_node)
            
            if complexity > self.max_complexity:
                func_name = self._get_function_name(func_node)
                message = (f"Function '{func_name}' has complexity {complexity}, "
                          f"exceeds maximum of {self.max_complexity}")
                suggestion = "Consider simplifying the logic or extracting complex conditions"
                
                issues.append(self.create_issue(message, func_node, file_path, suggestion))
        
        return issues
    
    def _calculate_complexity(self, node) -> int:
        """Calculate approximate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_types = {
            'if_statement', 'while_statement', 'for_statement',
            'case_statement', 'conditional_expression', 'switch_statement',
            'catch_clause', 'and', 'or'
        }
        
        if node.type in decision_types:
            complexity += 1
        
        for child in node.children:
            complexity += self._calculate_complexity(child) - 1
        
        return complexity
    
    def _find_functions(self, node):
        """Find all function definitions."""
        functions = []
        if node.type in ('function_definition', 'method_definition'):
            functions.append(node)
        for child in node.children:
            functions.extend(self._find_functions(child))
        return functions
    
    def _get_function_name(self, func_node) -> str:
        """Extract function name."""
        for child in func_node.children:
            if child.type in ('identifier', 'function_declarator'):
                if child.type == 'identifier':
                    return child.text.decode('utf8')
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        return subchild.text.decode('utf8')
        return '<unknown>'


def create_analyzer(language: str, config: Optional[Dict] = None) -> TreeSitterAnalyzer:
    """
    Create a configured analyzer for a language.
    
    Args:
        language: Programming language
        config: Optional configuration dict with rule parameters
        
    Returns:
        Configured TreeSitterAnalyzer
    """
    analyzer = TreeSitterAnalyzer(language)
    
    # Default config
    if config is None:
        config = {}
    
    # Add common rules
    max_func_length = config.get('max_function_length', 50)
    max_complexity = config.get('max_complexity', 10)
    
    analyzer.add_rule(FunctionLengthRule(max_func_length, language))
    analyzer.add_rule(ComplexityRule(max_complexity, language))
    
    # Language-specific rules can be added here
    
    return analyzer
