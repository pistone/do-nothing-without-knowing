"""
Metrics tracking for reviewer quality assessment.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import time

from .reviewer import ReviewResult


@dataclass
class QualityMetrics:
    """Quality metrics for the code reviewer."""
    total_mrs_reviewed: int
    total_files_analyzed: int
    total_issues_found: int
    average_issues_per_mr: float
    average_issues_per_file: float
    issues_by_severity: Dict[str, int]
    issues_by_category: Dict[str, int]
    average_analysis_time: float
    false_positive_rate: Optional[float] = None  # Requires human labels
    precision: Optional[float] = None  # Requires human labels
    recall: Optional[float] = None  # Requires human labels


class MetricsTracker:
    """Track and analyze reviewer quality metrics."""
    
    def __init__(self):
        self.results: List[ReviewResult] = []
        self.human_labels: Dict[int, Dict] = {}  # MR ID -> labels
    
    def add_result(self, result: ReviewResult):
        """Add a review result."""
        self.results.append(result)
    
    def add_human_labels(self, mr_id: int, labels: Dict[str, Any]):
        """
        Add human review labels for a specific MR.
        
        Args:
            mr_id: Merge request ID
            labels: Dict with 'true_positives', 'false_positives', 'false_negatives'
        """
        self.human_labels[mr_id] = labels
    
    def compute_metrics(self) -> QualityMetrics:
        """Compute aggregate quality metrics."""
        if not self.results:
            return QualityMetrics(
                total_mrs_reviewed=0,
                total_files_analyzed=0,
                total_issues_found=0,
                average_issues_per_mr=0.0,
                average_issues_per_file=0.0,
                issues_by_severity={},
                issues_by_category={},
                average_analysis_time=0.0
            )
        
        total_mrs = len(self.results)
        total_files = sum(r.analyzed_files for r in self.results)
        total_issues = sum(r.total_issues for r in self.results)
        
        # Aggregate severity and category counts
        all_severity = {}
        all_category = {}
        
        for result in self.results:
            for severity, count in result.issues_by_severity.items():
                all_severity[severity] = all_severity.get(severity, 0) + count
            for category, count in result.issues_by_category.items():
                all_category[category] = all_category.get(category, 0) + count
        
        # Compute averages
        avg_issues_per_mr = total_issues / total_mrs if total_mrs > 0 else 0
        avg_issues_per_file = total_issues / total_files if total_files > 0 else 0
        avg_time = sum(r.analysis_time for r in self.results) / total_mrs
        
        # Compute precision/recall if we have labels
        precision, recall, fpr = None, None, None
        if self.human_labels:
            precision, recall, fpr = self._compute_accuracy_metrics()
        
        return QualityMetrics(
            total_mrs_reviewed=total_mrs,
            total_files_analyzed=total_files,
            total_issues_found=total_issues,
            average_issues_per_mr=avg_issues_per_mr,
            average_issues_per_file=avg_issues_per_file,
            issues_by_severity=all_severity,
            issues_by_category=all_category,
            average_analysis_time=avg_time,
            false_positive_rate=fpr,
            precision=precision,
            recall=recall
        )
    
    def _compute_accuracy_metrics(self):
        """Compute precision, recall, and false positive rate."""
        total_tp = 0
        total_fp = 0
        total_fn = 0
        
        for mr_id, labels in self.human_labels.items():
            total_tp += labels.get('true_positives', 0)
            total_fp += labels.get('false_positives', 0)
            total_fn += labels.get('false_negatives', 0)
        
        # Precision: TP / (TP + FP)
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        
        # Recall: TP / (TP + FN)
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        
        # False Positive Rate: FP / (FP + TN)
        # For code review, we approximate this as FP / total_flagged
        fpr = total_fp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        
        return precision, recall, fpr
    
    def save_metrics(self, filepath: Path):
        """Save metrics to JSON file."""
        metrics = self.compute_metrics()
        
        data = {
            'timestamp': time.time(),
            'metrics': asdict(metrics),
            'results': [self._result_to_dict(r) for r in self.results]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _result_to_dict(self, result: ReviewResult) -> Dict:
        """Convert ReviewResult to dict (excluding full issues list)."""
        d = asdict(result)
        # Don't include full issues list in summary
        d['issues'] = len(result.issues)
        return d
    
    def load_metrics(self, filepath: Path):
        """Load metrics from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # TODO: Reconstruct results and labels from saved data
        pass
    
    def print_metrics(self, metrics: Optional[QualityMetrics] = None):
        """Print metrics in a readable format."""
        if metrics is None:
            metrics = self.compute_metrics()
        
        print("\n" + "="*60)
        print("REVIEWER QUALITY METRICS")
        print("="*60)
        
        print(f"\nOverall Statistics:")
        print(f"  MRs reviewed: {metrics.total_mrs_reviewed}")
        print(f"  Files analyzed: {metrics.total_files_analyzed}")
        print(f"  Total issues found: {metrics.total_issues_found}")
        print(f"  Avg issues per MR: {metrics.average_issues_per_mr:.2f}")
        print(f"  Avg issues per file: {metrics.average_issues_per_file:.2f}")
        print(f"  Avg analysis time: {metrics.average_analysis_time:.2f}s")
        
        if metrics.issues_by_severity:
            print(f"\nIssues by Severity:")
            for severity, count in sorted(metrics.issues_by_severity.items()):
                pct = (count / metrics.total_issues_found) * 100
                print(f"  {severity}: {count} ({pct:.1f}%)")
        
        if metrics.issues_by_category:
            print(f"\nIssues by Category:")
            for category, count in sorted(metrics.issues_by_category.items(), 
                                         key=lambda x: x[1], reverse=True):
                pct = (count / metrics.total_issues_found) * 100
                print(f"  {category}: {count} ({pct:.1f}%)")
        
        if metrics.precision is not None:
            print(f"\nAccuracy Metrics (vs Human Reviews):")
            print(f"  Precision: {metrics.precision:.2%}")
            print(f"  Recall: {metrics.recall:.2%}")
            print(f"  False Positive Rate: {metrics.false_positive_rate:.2%}")
            print(f"  F1 Score: {2 * (metrics.precision * metrics.recall) / (metrics.precision + metrics.recall):.2%}")
    
    def compare_with_baseline(self, baseline_file: Path):
        """Compare current metrics with a baseline."""
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
        
        baseline_metrics = QualityMetrics(**baseline_data['metrics'])
        current_metrics = self.compute_metrics()
        
        print("\n" + "="*60)
        print("COMPARISON WITH BASELINE")
        print("="*60)
        
        comparisons = [
            ('Issues per MR', baseline_metrics.average_issues_per_mr, 
             current_metrics.average_issues_per_mr),
            ('Analysis time', baseline_metrics.average_analysis_time, 
             current_metrics.average_analysis_time),
        ]
        
        if baseline_metrics.precision and current_metrics.precision:
            comparisons.extend([
                ('Precision', baseline_metrics.precision, current_metrics.precision),
                ('Recall', baseline_metrics.recall, current_metrics.recall),
            ])
        
        for name, baseline, current in comparisons:
            diff = current - baseline
            pct_change = (diff / baseline * 100) if baseline != 0 else 0
            direction = "↑" if diff > 0 else "↓" if diff < 0 else "="
            
            print(f"\n{name}:")
            print(f"  Baseline: {baseline:.3f}")
            print(f"  Current:  {current:.3f}")
            print(f"  Change:   {direction} {abs(diff):.3f} ({abs(pct_change):.1f}%)")


def create_tracker() -> MetricsTracker:
    """Create a new metrics tracker."""
    return MetricsTracker()
