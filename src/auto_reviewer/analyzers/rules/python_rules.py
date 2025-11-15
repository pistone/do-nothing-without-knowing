"""
Python specific analysis rules.
"""

from typing import List
from .tree_sitter_analyzer import AnalysisRule, CodeIssue


class BareExceptRule(AnalysisRule):
    """Check for bare except clauses."""
    
    def __init__(self):
        super().__init__(
            rule_id='BARE_EXCEPT',
            severity='warning',
            category='error_handling'
        )
    
    def check(self, root_node, code: str, file_path: str) -> List[CodeIssue]:
        issues = []
        bare_excepts = self._find_bare_excepts(root_node)
        
        for except_node in bare_excepts:
            message = "Bare 'except:' clause catches all exceptions"
            suggestion = "Specify exception types: except SpecificException:"
            issues.append(self.create_issue(message, except_node, file_path, suggestion))
        
        return issues
    
    def _find_bare_excepts(self, node):
        """Find bare except clauses."""
        excepts = []
        
        if node.type == 'except_clause':
            # Check if it has no exception type specified
            has_type = any(child.type in ('identifier', 'dotted_name') 
                          for child in node.children)
            if not has_type:
                excepts.append(node)
        
        for child in node.children:
            excepts.extend(self._find_bare_excepts(child))
        
        return excepts


class MutableDefaultArgRule(AnalysisRule):
    """Check for mutable default arguments."""
    
    def __init__(self):
        super().__init__(
            rule_id='MUTABLE_DEFAULT_ARG',
            severity='warning',
            category='potential_bug'
        )
    
    def check(self, root_node, code: str, file_path: str) -> List[CodeIssue]:
        issues = []
        functions = self._find_functions(root_node)
        
        for func_node in functions:
            mutable_defaults = self._find_mutable_defaults(func_node)
            
            for default_node in mutable_defaults:
                func_name = self._get_function_name(func_node)
                message = f"Function '{func_name}' has mutable default argument"
                suggestion = "Use None as default and initialize inside function"
                issues.append(self.create_issue(message, default_node, file_path, suggestion))
        
        return issues
    
    def _find_functions(self, node):
        """Find all function definitions."""
        functions = []
        if node.type == 'function_definition':
            functions.append(node)
        for child in node.children:
            functions.extend(self._find_functions(child))
        return functions
    
    def _find_mutable_defaults(self, func_node):
        """Find mutable default arguments (list, dict, set)."""
        mutable_defaults = []
        
        for child in func_node.children:
            if child.type == 'parameters':
                for param in child.children:
                    if param.type == 'default_parameter':
                        default_value = self._get_default_value(param)
                        if default_value and default_value.type in ('list', 'dictionary', 'set'):
                            mutable_defaults.append(default_value)
        
        return mutable_defaults
    
    def _get_default_value(self, param_node):
        """Get the default value node from parameter."""
        for child in param_node.children:
            if child.type in ('list', 'dictionary', 'set'):
                return child
        return None
    
    def _get_function_name(self, func_node) -> str:
        """Extract function name."""
        for child in func_node.children:
            if child.type == 'identifier':
                return child.text.decode('utf8')
        return '<unknown>'


class UnusedImportRule(AnalysisRule):
    """Check for unused imports (simplified)."""
    
    def __init__(self):
        super().__init__(
            rule_id='UNUSED_IMPORT',
            severity='info',
            category='style'
        )
    
    def check(self, root_node, code: str, file_path: str) -> List[CodeIssue]:
        issues = []
        
        # Get all imports
        imports = self._find_imports(root_node)
        
        # Get all identifiers used in code
        used_names = self._find_used_identifiers(root_node)
        
        # Check which imports are not used
        for import_node in imports:
            imported_names = self._get_imported_names(import_node)
            
            for name in imported_names:
                if name not in used_names:
                    message = f"Imported name '{name}' is not used"
                    suggestion = f"Remove unused import or add to __all__ if re-exported"
                    issues.append(self.create_issue(message, import_node, file_path, suggestion))
        
        return issues
    
    def _find_imports(self, node):
        """Find all import statements."""
        imports = []
        if node.type in ('import_statement', 'import_from_statement'):
            imports.append(node)
        for child in node.children:
            imports.extend(self._find_imports(child))
        return imports
    
    def _get_imported_names(self, import_node):
        """Extract names imported by an import statement."""
        names = []
        for child in import_node.children:
            if child.type in ('dotted_name', 'identifier'):
                # Get the final name that's actually imported
                name_parts = child.text.decode('utf8').split('.')
                names.append(name_parts[-1])
            elif child.type == 'aliased_import':
                # For "import x as y", we care about y
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        # The alias is what's actually used
                        alias = subchild
                names.append(alias.text.decode('utf8') if alias else None)
        return [n for n in names if n]
    
    def _find_used_identifiers(self, node):
        """Find all identifiers used in the code (excluding imports)."""
        identifiers = set()
        
        # Skip the import statements themselves
        if node.type not in ('import_statement', 'import_from_statement'):
            if node.type == 'identifier':
                identifiers.add(node.text.decode('utf8'))
            
            for child in node.children:
                identifiers.update(self._find_used_identifiers(child))
        
        return identifiers


class MissingDocstringRule(AnalysisRule):
    """Check for missing docstrings in functions/classes."""
    
    def __init__(self):
        super().__init__(
            rule_id='MISSING_DOCSTRING',
            severity='info',
            category='documentation'
        )
    
    def check(self, root_node, code: str, file_path: str) -> List[CodeIssue]:
        issues = []
        
        # Find functions and classes
        functions = self._find_functions(root_node)
        classes = self._find_classes(root_node)
        
        for func_node in functions:
            if not self._has_docstring(func_node):
                func_name = self._get_function_name(func_node)
                # Skip private functions and very short functions
                if not func_name.startswith('_') and self._is_significant(func_node):
                    message = f"Public function '{func_name}' missing docstring"
                    suggestion = 'Add docstring describing parameters, returns, and behavior'
                    issues.append(self.create_issue(message, func_node, file_path, suggestion))
        
        for class_node in classes:
            if not self._has_docstring(class_node):
                class_name = self._get_class_name(class_node)
                message = f"Class '{class_name}' missing docstring"
                suggestion = 'Add docstring describing the class purpose and attributes'
                issues.append(self.create_issue(message, class_node, file_path, suggestion))
        
        return issues
    
    def _find_functions(self, node):
        """Find all function definitions."""
        functions = []
        if node.type == 'function_definition':
            functions.append(node)
        for child in node.children:
            functions.extend(self._find_functions(child))
        return functions
    
    def _find_classes(self, node):
        """Find all class definitions."""
        classes = []
        if node.type == 'class_definition':
            classes.append(node)
        for child in node.children:
            classes.extend(self._find_classes(child))
        return classes
    
    def _has_docstring(self, node) -> bool:
        """Check if node has a docstring."""
        for child in node.children:
            if child.type == 'block':
                for stmt in child.children:
                    if stmt.type == 'expression_statement':
                        for expr_child in stmt.children:
                            if expr_child.type == 'string':
                                return True
        return False
    
    def _is_significant(self, func_node) -> bool:
        """Check if function is significant enough to require docstring."""
        # Simple heuristic: more than 3 lines
        lines = func_node.end_point[0] - func_node.start_point[0]
        return lines > 3
    
    def _get_function_name(self, func_node) -> str:
        """Extract function name."""
        for child in func_node.children:
            if child.type == 'identifier':
                return child.text.decode('utf8')
        return '<unknown>'
    
    def _get_class_name(self, class_node) -> str:
        """Extract class name."""
        for child in class_node.children:
            if child.type == 'identifier':
                return child.text.decode('utf8')
        return '<unknown>'


def get_python_rules() -> List[AnalysisRule]:
    """Get all Python specific rules."""
    return [
        BareExceptRule(),
        MutableDefaultArgRule(),
        UnusedImportRule(),
        MissingDocstringRule()
    ]
