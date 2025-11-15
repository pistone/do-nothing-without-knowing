"""
Parser for git diffs to extract code changes.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from unidiff import PatchSet
import io


@dataclass
class CodeChange:
    """Represents a code change in a diff."""
    file_path: str
    old_line_start: int
    old_line_end: int
    new_line_start: int
    new_line_end: int
    added_lines: List[Tuple[int, str]]  # (line_number, content)
    removed_lines: List[Tuple[int, str]]  # (line_number, content)
    context_lines: List[Tuple[int, str]]  # (line_number, content)


@dataclass
class FileDiff:
    """Represents all changes in a single file."""
    file_path: str
    is_new: bool
    is_deleted: bool
    is_renamed: bool
    changes: List[CodeChange]


class DiffParser:
    """Parser for git diffs."""
    
    def parse(self, diff_text: str) -> List[FileDiff]:
        """
        Parse a git diff string.
        
        Args:
            diff_text: Git diff output
            
        Returns:
            List of FileDiff objects
        """
        if not diff_text or not diff_text.strip():
            return []
        
        try:
            patch_set = PatchSet(io.StringIO(diff_text))
            return [self._parse_patched_file(pf) for pf in patch_set]
        except Exception as e:
            print(f"Error parsing diff: {e}")
            return []
    
    def _parse_patched_file(self, patched_file) -> FileDiff:
        """Parse a single patched file from unidiff."""
        changes = []
        
        for hunk in patched_file:
            change = self._parse_hunk(hunk, patched_file.path)
            changes.append(change)
        
        return FileDiff(
            file_path=patched_file.path,
            is_new=patched_file.is_added_file,
            is_deleted=patched_file.is_removed_file,
            is_renamed=patched_file.is_rename,
            changes=changes
        )
    
    def _parse_hunk(self, hunk, file_path: str) -> CodeChange:
        """Parse a single hunk (chunk of changes)."""
        added_lines = []
        removed_lines = []
        context_lines = []
        
        for line in hunk:
            if line.is_added:
                added_lines.append((line.target_line_no, line.value))
            elif line.is_removed:
                removed_lines.append((line.source_line_no, line.value))
            else:  # context line
                context_lines.append((line.target_line_no or line.source_line_no, line.value))
        
        return CodeChange(
            file_path=file_path,
            old_line_start=hunk.source_start,
            old_line_end=hunk.source_start + hunk.source_length - 1,
            new_line_start=hunk.target_start,
            new_line_end=hunk.target_start + hunk.target_length - 1,
            added_lines=added_lines,
            removed_lines=removed_lines,
            context_lines=context_lines
        )
    
    def get_added_code(self, file_diff: FileDiff) -> str:
        """
        Extract all added code from a file diff.
        
        Args:
            file_diff: FileDiff object
            
        Returns:
            Combined string of all added code
        """
        lines = []
        for change in file_diff.changes:
            for _, content in change.added_lines:
                lines.append(content)
        return ''.join(lines)
    
    def get_changed_line_numbers(self, file_diff: FileDiff) -> List[int]:
        """
        Get all line numbers that were changed (added or modified).
        
        Args:
            file_diff: FileDiff object
            
        Returns:
            List of line numbers in the new file
        """
        line_numbers = set()
        for change in file_diff.changes:
            for line_no, _ in change.added_lines:
                if line_no is not None:
                    line_numbers.add(line_no)
        return sorted(line_numbers)
    
    def reconstruct_file_content(self, file_diff: FileDiff) -> Optional[str]:
        """
        Reconstruct the new file content from diff.
        
        Args:
            file_diff: FileDiff object
            
        Returns:
            Reconstructed file content or None if not possible
        """
        if file_diff.is_deleted:
            return None
        
        # This is a simplified version - for complete reconstruction,
        # you'd need the original file content
        lines = []
        for change in file_diff.changes:
            # Add context lines and new lines
            all_lines = sorted(
                [(ln, content) for ln, content in change.context_lines] +
                [(ln, content) for ln, content in change.added_lines],
                key=lambda x: x[0]
            )
            for _, content in all_lines:
                lines.append(content)
        
        return ''.join(lines) if lines else None


def parse_diff(diff_text: str) -> List[FileDiff]:
    """
    Convenience function to parse a diff.
    
    Args:
        diff_text: Git diff output
        
    Returns:
        List of FileDiff objects
    """
    parser = DiffParser()
    return parser.parse(diff_text)
