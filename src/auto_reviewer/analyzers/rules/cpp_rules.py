"""
C/C++ specific analysis rules.
"""

from typing import List, Optional
from .tree_sitter_analyzer import AnalysisRule, CodeIssue


class MissingReturnRule(AnalysisRule):
    """Check for functions that might be missing return statements."""
    
    def __init__(self):
        super().__init__(
            rule_id='MISSING_RETURN',
            severity='error',
            category='potential_bug'
        )
    
    def check(self, root_node, code: str, file_path: str) -> List[CodeIssue]:
        issues = []
        functions = self._find_non_void_functions(root_node)
        
        for func_node in functions:
            if not self._has_return_statement(func_node):
                func_name = self._get_function_name(func_node)
                message = f"Function '{func_name}' may be missing a return statement"
                suggestion = "Ensure all code paths return a value"
                issues.append(self.create_issue(message, func_node, file_path, suggestion))
        
        return issues
    
    def _find_non_void_functions(self, node):
        """Find functions with non-void return types."""
        functions = []
        
        if node.type == 'function_definition':
            # Check if return type is not void
            return_type = self._get_return_type(node)
            if return_type and return_type != 'void':
                functions.append(node)
        
        for child in node.children:
            functions.extend(self._find_non_void_functions(child))
        
        return functions
    
    def _get_return_type(self, func_node) -> Optional[str]:
        """Extract return type from function."""
        for child in func_node.children:
            if child.type in ('type_identifier', 'primitive_type'):
                return child.text.decode('utf8')
        return None
    
    def _has_return_statement(self, func_node) -> bool:
        """Check if function has at least one return statement."""
        if func_node.type == 'return_statement':
            return True
        
        for child in func_node.children:
            if self._has_return_statement(child):
                return True
        
        return False
    
    def _get_function_name(self, func_node) -> str:
        """Extract function name."""
        for child in func_node.children:
            if child.type == 'function_declarator':
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        return subchild.text.decode('utf8')
        return '<unknown>'


class ResourceLeakRule(AnalysisRule):
    """Check for potential resource leaks (simplified version)."""
    
    def __init__(self):
        super().__init__(
            rule_id='RESOURCE_LEAK',
            severity='warning',
            category='resource_management'
        )
        self.alloc_functions = {'malloc', 'calloc', 'realloc', 'new', 'fopen'}
        self.free_functions = {'free', 'delete', 'fclose'}
    
    def check(self, root_node, code: str, file_path: str) -> List[CodeIssue]:
        issues = []
        
        # Find all functions
        functions = self._find_functions(root_node)
        
        for func_node in functions:
            allocations = self._find_allocations(func_node)
            frees = self._find_frees(func_node)
            
            # Simple heuristic: if more allocations than frees, flag it
            if len(allocations) > len(frees):
                func_name = self._get_function_name(func_node)
                message = (f"Function '{func_name}' has {len(allocations)} allocations "
                          f"but only {len(frees)} deallocations")
                suggestion = "Ensure all allocated resources are properly freed"
                issues.append(self.create_issue(message, func_node, file_path, suggestion))
        
        return issues
    
    def _find_functions(self, node):
        """Find all function definitions."""
        functions = []
        if node.type == 'function_definition':
            functions.append(node)
        for child in node.children:
            functions.extend(self._find_functions(child))
        return functions
    
    def _find_allocations(self, node):
        """Find resource allocation calls."""
        allocations = []
        
        if node.type == 'call_expression':
            func_name = self._get_call_name(node)
            if func_name in self.alloc_functions:
                allocations.append(node)
        
        for child in node.children:
            allocations.extend(self._find_allocations(child))
        
        return allocations
    
    def _find_frees(self, node):
        """Find resource deallocation calls."""
        frees = []
        
        if node.type == 'call_expression':
            func_name = self._get_call_name(node)
            if func_name in self.free_functions:
                frees.append(node)
        
        for child in node.children:
            frees.extend(self._find_frees(child))
        
        return frees
    
    def _get_call_name(self, call_node) -> Optional[str]:
        """Extract function name from call expression."""
        for child in call_node.children:
            if child.type == 'identifier':
                return child.text.decode('utf8')
        return None
    
    def _get_function_name(self, func_node) -> str:
        """Extract function name."""
        for child in func_node.children:
            if child.type == 'function_declarator':
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        return subchild.text.decode('utf8')
        return '<unknown>'


class NullCheckRule(AnalysisRule):
    """Check for pointer dereferences without null checks."""
    
    def __init__(self):
        super().__init__(
            rule_id='MISSING_NULL_CHECK',
            severity='warning',
            category='safety'
        )
    
    def check(self, root_node, code: str, file_path: str) -> List[CodeIssue]:
        issues = []
        
        # This is a simplified version - would need dataflow analysis for production
        # For now, just flag dereferences of function parameters
        functions = self._find_functions(root_node)
        
        for func_node in functions:
            pointer_params = self._find_pointer_parameters(func_node)
            derefs = self._find_dereferences(func_node)
            null_checks = self._find_null_checks(func_node)
            
            # Check if pointer params are dereferenced without null checks
            for param in pointer_params:
                param_name = param.text.decode('utf8')
                is_checked = any(param_name in check for check in null_checks)
                is_derefed = any(param_name in deref for deref in derefs)
                
                if is_derefed and not is_checked:
                    message = f"Pointer parameter '{param_name}' dereferenced without null check"
                    suggestion = f"Add null check: if ({param_name} == nullptr) {{ return; }}"
                    issues.append(self.create_issue(message, param, file_path, suggestion))
        
        return issues
    
    def _find_functions(self, node):
        """Find all function definitions."""
        functions = []
        if node.type == 'function_definition':
            functions.append(node)
        for child in node.children:
            functions.extend(self._find_functions(child))
        return functions
    
    def _find_pointer_parameters(self, func_node):
        """Find pointer parameters in function."""
        # Simplified - would need proper type analysis
        params = []
        for child in func_node.children:
            if child.type == 'parameter_list':
                for param in child.children:
                    if '*' in param.text.decode('utf8'):
                        params.append(param)
        return params
    
    def _find_dereferences(self, node):
        """Find pointer dereferences."""
        derefs = []
        if node.type == 'pointer_expression':
            derefs.append(node.text.decode('utf8'))
        for child in node.children:
            derefs.extend(self._find_dereferences(child))
        return derefs
    
    def _find_null_checks(self, node):
        """Find null/nullptr checks."""
        checks = []
        # Look for comparisons with NULL/nullptr
        if node.type == 'binary_expression':
            text = node.text.decode('utf8')
            if 'nullptr' in text or 'NULL' in text or '== 0' in text:
                checks.append(text)
        for child in node.children:
            checks.extend(self._find_null_checks(child))
        return checks


def get_cpp_rules() -> List[AnalysisRule]:
    """Get all C++ specific rules."""
    return [
        MissingReturnRule(),
        ResourceLeakRule(),
        NullCheckRule()
    ]
