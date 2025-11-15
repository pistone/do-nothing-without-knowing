"""
Parser for GitLab Merge Request JSON files.
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path


@dataclass
class MRFile:
    """Represents a file changed in a merge request."""
    old_path: str
    new_path: str
    old_content: Optional[str]
    new_content: Optional[str]
    diff: str
    is_new: bool
    is_deleted: bool
    is_renamed: bool


@dataclass
class MRMetadata:
    """Metadata about the merge request."""
    id: int
    iid: int
    title: str
    description: str
    author: str
    created_at: str
    updated_at: str
    source_branch: str
    target_branch: str
    state: str
    web_url: str


@dataclass
class MergeRequest:
    """Complete merge request with metadata and changes."""
    metadata: MRMetadata
    files: List[MRFile]
    raw_data: Dict[str, Any]


class MRParser:
    """Parser for GitLab merge request JSON files."""
    
    def __init__(self):
        self.supported_extensions = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', 
                                     '.py', '.java', '.js', '.ts', '.go'}
    
    def parse_file(self, filepath: Path) -> MergeRequest:
        """
        Parse a GitLab MR JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            MergeRequest object with parsed data
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self.parse_dict(data)
    
    def parse_dict(self, data: Dict[str, Any]) -> MergeRequest:
        """
        Parse a GitLab MR from a dictionary.
        
        Args:
            data: Dictionary containing MR data
            
        Returns:
            MergeRequest object
        """
        metadata = self._parse_metadata(data)
        files = self._parse_changes(data)
        
        return MergeRequest(
            metadata=metadata,
            files=files,
            raw_data=data
        )
    
    def _parse_metadata(self, data: Dict[str, Any]) -> MRMetadata:
        """Extract metadata from MR data."""
        return MRMetadata(
            id=data.get('id', 0),
            iid=data.get('iid', 0),
            title=data.get('title', ''),
            description=data.get('description', ''),
            author=data.get('author', {}).get('username', 'unknown'),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            source_branch=data.get('source_branch', ''),
            target_branch=data.get('target_branch', ''),
            state=data.get('state', ''),
            web_url=data.get('web_url', '')
        )
    
    def _parse_changes(self, data: Dict[str, Any]) -> List[MRFile]:
        """Extract file changes from MR data."""
        files = []
        
        # GitLab API may provide changes in different formats
        changes = data.get('changes', [])
        if not changes and 'diffs' in data:
            changes = data['diffs']
        
        for change in changes:
            # Skip files we don't analyze
            new_path = change.get('new_path', '')
            if not self._should_analyze(new_path):
                continue
            
            mr_file = MRFile(
                old_path=change.get('old_path', ''),
                new_path=new_path,
                old_content=None,  # Will be populated if needed
                new_content=None,  # Will be populated if needed
                diff=change.get('diff', ''),
                is_new=change.get('new_file', False),
                is_deleted=change.get('deleted_file', False),
                is_renamed=change.get('renamed_file', False)
            )
            files.append(mr_file)
        
        return files
    
    def _should_analyze(self, filepath: str) -> bool:
        """
        Determine if a file should be analyzed based on extension.
        
        Args:
            filepath: Path to the file
            
        Returns:
            True if file should be analyzed
        """
        if not filepath:
            return False
        
        path = Path(filepath)
        return path.suffix in self.supported_extensions
    
    def get_file_language(self, filepath: str) -> Optional[str]:
        """
        Determine the programming language from file extension.
        
        Args:
            filepath: Path to the file
            
        Returns:
            Language name or None
        """
        ext = Path(filepath).suffix.lower()
        
        language_map = {
            '.c': 'c',
            '.h': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.hpp': 'cpp',
            '.py': 'python',
            '.java': 'java',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go'
        }
        
        return language_map.get(ext)


def load_mr(filepath: Path) -> MergeRequest:
    """
    Convenience function to load a merge request from file.
    
    Args:
        filepath: Path to MR JSON file
        
    Returns:
        Parsed MergeRequest
    """
    parser = MRParser()
    return parser.parse_file(filepath)
