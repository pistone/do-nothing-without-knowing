"""
Main code reviewer orchestration.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import time
from pathlib import Path

from .parsers import MergeRequest, MRParser, DiffParser
from .analyzers import create_analyzer, CodeIssue


@dataclass
class ReviewResult:
    """Results from reviewing a merge request."""
    mr_id: int
    mr_title: str
    total_files: int
    analyzed_files: int
    total_issues: int
    issues_by_severity: Dict[str, int]
    issues_by_category: Dict[str, int]
    issues: List[CodeIssue]
    analysis_time: float
    files_with_issues: List[str]


class CodeReviewer:
    """
    Main code reviewer that orchestrates analysis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the reviewer.
        
        Args:
            config: Configuration dict with analyzer settings
        """
        self.config = config or {}
        self.mr_parser = MRParser()
        self.diff_parser = DiffParser()
        self.analyzers = {}  # Cache analyzers by language
    
    def review_mr(self, mr: MergeRequest, verbose: bool = False) -> ReviewResult:
        """
        Review a merge request.
        
        Args:
            mr: MergeRequest object to review
            verbose: Print detailed progress
            
        Returns:
            ReviewResult with found issues
        """
        start_time = time.time()
        
        all_issues = []
        analyzed_files = 0
        files_with_issues = []
        
        if verbose:
            print(f"\nReviewing MR #{mr.metadata.iid}: {mr.metadata.title}")
            print(f"Analyzing {len(mr.files)} files...")
        
        for mr_file in mr.files:
            if verbose:
                print(f"  {mr_file.new_path}...", end=" ")
            
            # Get language
            language = self.mr_parser.get_file_language(mr_file.new_path)
            if not language:
                if verbose:
                    print("skipped (unsupported)")
                continue
            
            # Parse diff to get actual code
            file_diffs = self.diff_parser.parse(mr_file.diff)
            if not file_diffs:
                if verbose:
                    print("skipped (no diff)")
                continue
            
            file_diff = file_diffs[0]
            
            # Get code to analyze (added code)
            code = self.diff_parser.get_added_code(file_diff)
            if not code or not code.strip():
                if verbose:
                    print("skipped (no added code)")
                continue
            
            # Get or create analyzer for this language
            analyzer = self._get_analyzer(language)
            
            # Analyze the code
            try:
                issues = analyzer.analyze_code(code, mr_file.new_path)
                all_issues.extend(issues)
                analyzed_files += 1
                
                if issues:
                    files_with_issues.append(mr_file.new_path)
                
                if verbose:
                    print(f"found {len(issues)} issues")
            except Exception as e:
                if verbose:
                    print(f"ERROR: {e}")
        
        analysis_time = time.time() - start_time
        
        # Aggregate statistics
        issues_by_severity = self._count_by_field(all_issues, 'severity')
        issues_by_category = self._count_by_field(all_issues, 'category')
        
        result = ReviewResult(
            mr_id=mr.metadata.iid,
            mr_title=mr.metadata.title,
            total_files=len(mr.files),
            analyzed_files=analyzed_files,
            total_issues=len(all_issues),
            issues_by_severity=issues_by_severity,
            issues_by_category=issues_by_category,
            issues=all_issues,
            analysis_time=analysis_time,
            files_with_issues=files_with_issues
        )
        
        if verbose:
            self._print_summary(result)
        
        return result
    
    def review_mr_file(self, filepath: Path, verbose: bool = False) -> ReviewResult:
        """
        Review a merge request from a JSON file.
        
        Args:
            filepath: Path to MR JSON file
            verbose: Print detailed progress
            
        Returns:
            ReviewResult
        """
        mr = self.mr_parser.parse_file(filepath)
        return self.review_mr(mr, verbose)
    
    def _get_analyzer(self, language: str):
        """Get or create analyzer for language."""
        if language not in self.analyzers:
            # Get language-specific config
            lang_config = self.config.get(language, {})
            
            # Create and configure analyzer
            analyzer = create_analyzer(language, lang_config)
            
            # Add language-specific rules
            if language in ['c', 'cpp']:
                from .analyzers.rules.cpp_rules import get_cpp_rules
                for rule in get_cpp_rules():
                    analyzer.add_rule(rule)
            elif language == 'python':
                from .analyzers.rules.python_rules import get_python_rules
                for rule in get_python_rules():
                    analyzer.add_rule(rule)
            
            self.analyzers[language] = analyzer
        
        return self.analyzers[language]
    
    def _count_by_field(self, issues: List[CodeIssue], field: str) -> Dict[str, int]:
        """Count issues by a specific field."""
        counts = {}
        for issue in issues:
            value = getattr(issue, field)
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def _print_summary(self, result: ReviewResult):
        """Print review summary."""
        print(f"\n{'='*60}")
        print(f"Review Summary for MR #{result.mr_id}")
        print(f"{'='*60}")
        print(f"Title: {result.mr_title}")
        print(f"Files analyzed: {result.analyzed_files}/{result.total_files}")
        print(f"Total issues found: {result.total_issues}")
        print(f"Analysis time: {result.analysis_time:.2f}s")
        
        if result.issues_by_severity:
            print(f"\nBy Severity:")
            for severity, count in sorted(result.issues_by_severity.items()):
                print(f"  {severity}: {count}")
        
        if result.issues_by_category:
            print(f"\nBy Category:")
            for category, count in sorted(result.issues_by_category.items()):
                print(f"  {category}: {count}")
        
        if result.files_with_issues:
            print(f"\nFiles with issues ({len(result.files_with_issues)}):")
            for filepath in result.files_with_issues[:10]:
                print(f"  - {filepath}")
            if len(result.files_with_issues) > 10:
                print(f"  ... and {len(result.files_with_issues) - 10} more")
    
    def format_issues_for_gitlab(self, result: ReviewResult) -> List[Dict[str, Any]]:
        """
        Format issues as GitLab comments.
        
        Args:
            result: ReviewResult
            
        Returns:
            List of comment dicts suitable for GitLab API
        """
        comments = []
        
        for issue in result.issues:
            # Group by file and line
            comment = {
                'position': {
                    'new_path': issue.file_path,
                    'new_line': issue.line_number
                },
                'body': self._format_issue_comment(issue)
            }
            comments.append(comment)
        
        return comments
    
    def _format_issue_comment(self, issue: CodeIssue) -> str:
        """Format a single issue as a comment."""
        emoji = {
            'error': '🔴',
            'warning': '⚠️',
            'info': 'ℹ️'
        }.get(issue.severity, '•')
        
        parts = [
            f"{emoji} **{issue.severity.upper()}**: {issue.message}",
            f"\n**Category**: {issue.category}",
            f"\n**Rule**: `{issue.rule_id}`"
        ]
        
        if issue.suggestion:
            parts.append(f"\n\n💡 **Suggestion**: {issue.suggestion}")
        
        return ''.join(parts)
