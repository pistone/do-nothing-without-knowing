#!/usr/bin/env python3
"""
Batch review multiple MRs and generate quality metrics.
"""

import argparse
import sys
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from auto_reviewer.reviewer import CodeReviewer
from auto_reviewer.metrics import MetricsTracker
from auto_reviewer.parsers import load_mr


def find_mr_files(directory: Path) -> List[Path]:
    """Find all MR JSON files in directory."""
    return sorted(directory.glob('*.json'))


def review_batch(mr_files: List[Path], config: dict, verbose: bool = False):
    """
    Review a batch of MRs.
    
    Args:
        mr_files: List of MR JSON files
        config: Reviewer configuration
        verbose: Verbose output
        
    Returns:
        MetricsTracker with results
    """
    reviewer = CodeReviewer(config)
    tracker = MetricsTracker()
    
    print(f"\n🔍 Reviewing {len(mr_files)} merge requests...")
    print("=" * 80)
    
    for i, mr_file in enumerate(mr_files, 1):
        print(f"\n[{i}/{len(mr_files)}] Processing {mr_file.name}...")
        
        try:
            result = reviewer.review_mr_file(mr_file, verbose=verbose)
            tracker.add_result(result)
            
            print(f"  ✓ Found {result.total_issues} issues in {result.analyzed_files} files")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    return tracker


def main():
    parser = argparse.ArgumentParser(
        description='Batch review multiple merge requests and generate metrics'
    )
    parser.add_argument(
        'mr_directory',
        type=Path,
        help='Directory containing MR JSON files'
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to config YAML file'
    )
    parser.add_argument(
        '--output-report',
        type=Path,
        default=Path('quality_metrics.json'),
        help='Output metrics report (default: quality_metrics.json)'
    )
    parser.add_argument(
        '--baseline',
        type=Path,
        help='Baseline metrics file for comparison'
    )
    parser.add_argument(
        '--human-labels',
        type=Path,
        help='JSON file with human review labels for accuracy metrics'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Check directory exists
    if not args.mr_directory.exists():
        print(f"Error: Directory not found: {args.mr_directory}")
        sys.exit(1)
    
    # Find MR files
    mr_files = find_mr_files(args.mr_directory)
    if not mr_files:
        print(f"Error: No JSON files found in {args.mr_directory}")
        sys.exit(1)
    
    print(f"Found {len(mr_files)} MR files")
    
    # Load config if provided
    config = {}
    if args.config and args.config.exists():
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f)
    
    # Load human labels if provided
    if args.human_labels and args.human_labels.exists():
        import json
        with open(args.human_labels) as f:
            labels_data = json.load(f)
        print(f"Loaded human labels for {len(labels_data)} MRs")
    else:
        labels_data = {}
    
    # Review all MRs
    tracker = review_batch(mr_files, config, verbose=args.verbose)
    
    # Add human labels if available
    for mr_id, labels in labels_data.items():
        tracker.add_human_labels(int(mr_id), labels)
    
    # Compute and print metrics
    print("\n" + "=" * 80)
    print("GENERATING QUALITY METRICS")
    print("=" * 80)
    
    metrics = tracker.compute_metrics()
    tracker.print_metrics(metrics)
    
    # Save metrics
    tracker.save_metrics(args.output_report)
    print(f"\n✓ Metrics report saved to {args.output_report}")
    
    # Compare with baseline if provided
    if args.baseline and args.baseline.exists():
        tracker.compare_with_baseline(args.baseline)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total MRs reviewed: {metrics.total_mrs_reviewed}")
    print(f"Total issues found: {metrics.total_issues_found}")
    print(f"Avg issues per MR: {metrics.average_issues_per_mr:.2f}")
    
    if metrics.precision is not None:
        print(f"Precision: {metrics.precision:.1%}")
        print(f"Recall: {metrics.recall:.1%}")
    
    print("\nNext steps:")
    print("1. Review the issues found in individual MRs")
    print("2. Label true/false positives for accuracy metrics")
    print("3. Adjust rules and thresholds based on findings")
    print("4. Re-run batch review to measure improvements")


if __name__ == '__main__':
    main()
