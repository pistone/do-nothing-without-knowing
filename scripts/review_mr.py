#!/usr/bin/env python3
"""
Review a single merge request from a JSON file.
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auto_reviewer.reviewer import CodeReviewer
from auto_reviewer.parsers import load_mr


def print_issues(result):
    """Print issues in a readable format."""
    if not result.issues:
        print("\n✨ No issues found!")
        return
    
    print(f"\n{'='*80}")
    print(f"ISSUES FOUND: {len(result.issues)}")
    print(f"{'='*80}\n")
    
    # Group issues by file
    by_file = {}
    for issue in result.issues:
        if issue.file_path not in by_file:
            by_file[issue.file_path] = []
        by_file[issue.file_path].append(issue)
    
    # Print issues grouped by file
    for filepath, issues in sorted(by_file.items()):
        print(f"\n📄 {filepath}")
        print(f"{'─'*80}")
        
        for issue in sorted(issues, key=lambda x: x.line_number):
            # Severity emoji
            emoji = {
                'error': '🔴',
                'warning': '⚠️',
                'info': 'ℹ️'
            }.get(issue.severity, '•')
            
            print(f"\n  {emoji} Line {issue.line_number} [{issue.severity.upper()}]")
            print(f"     {issue.message}")
            print(f"     Category: {issue.category} | Rule: {issue.rule_id}")
            
            if issue.suggestion:
                print(f"     💡 {issue.suggestion}")


def save_gitlab_comments(result, output_file: Path):
    """Save issues as GitLab comment format."""
    reviewer = CodeReviewer()
    comments = reviewer.format_issues_for_gitlab(result)
    
    with open(output_file, 'w') as f:
        json.dump(comments, f, indent=2)
    
    print(f"\n✓ GitLab comments saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Review a merge request from a JSON file'
    )
    parser.add_argument(
        'mr_file',
        type=Path,
        help='Path to MR JSON file'
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to config YAML file'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--gitlab-comments',
        type=Path,
        help='Save issues as GitLab comments to this file'
    )
    parser.add_argument(
        '--json-output',
        type=Path,
        help='Save full results as JSON'
    )
    
    args = parser.parse_args()
    
    # Check file exists
    if not args.mr_file.exists():
        print(f"Error: File not found: {args.mr_file}")
        sys.exit(1)
    
    # Load config if provided
    config = {}
    if args.config and args.config.exists():
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f)
    
    # Create reviewer
    reviewer = CodeReviewer(config)
    
    # Review the MR
    print(f"\n🔍 Reviewing {args.mr_file}...")
    result = reviewer.review_mr_file(args.mr_file, verbose=args.verbose)
    
    # Print issues
    if not args.verbose:
        # Summary was already printed if verbose
        print(f"\n{'='*60}")
        print(f"Review Complete")
        print(f"{'='*60}")
        print(f"Files analyzed: {result.analyzed_files}/{result.total_files}")
        print(f"Issues found: {result.total_issues}")
        print(f"Analysis time: {result.analysis_time:.2f}s")
    
    print_issues(result)
    
    # Save outputs
    if args.gitlab_comments:
        save_gitlab_comments(result, args.gitlab_comments)
    
    if args.json_output:
        from auto_reviewer.metrics import MetricsTracker
        tracker = MetricsTracker()
        tracker.add_result(result)
        tracker.save_metrics(args.json_output)
        print(f"✓ Full results saved to {args.json_output}")
    
    # Exit with non-zero if errors found
    has_errors = any(issue.severity == 'error' for issue in result.issues)
    sys.exit(1 if has_errors else 0)


if __name__ == '__main__':
    main()
