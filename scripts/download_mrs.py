#!/usr/bin/env python3
"""
Download merge requests from GitLab for local testing.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import gitlab


def download_mr(gl, project_id: int, mr_iid: int, output_dir: Path) -> bool:
    """
    Download a single merge request.
    
    Args:
        gl: GitLab connection
        project_id: GitLab project ID
        mr_iid: Merge request IID
        output_dir: Output directory
        
    Returns:
        True if successful
    """
    try:
        # Get project
        project = gl.projects.get(project_id)
        
        # Get merge request
        mr = project.mergerequests.get(mr_iid)
        
        # Get changes/diffs
        changes = mr.changes()
        
        # Build MR data structure
        mr_data = {
            'id': mr.id,
            'iid': mr.iid,
            'title': mr.title,
            'description': mr.description,
            'author': {
                'username': mr.author['username'],
                'name': mr.author['name']
            },
            'created_at': mr.created_at,
            'updated_at': mr.updated_at,
            'source_branch': mr.source_branch,
            'target_branch': mr.target_branch,
            'state': mr.state,
            'web_url': mr.web_url,
            'changes': changes.get('changes', [])
        }
        
        # Save to file
        output_file = output_dir / f"mr_{mr_iid}.json"
        with open(output_file, 'w') as f:
            json.dump(mr_data, f, indent=2)
        
        print(f"✓ Downloaded MR !{mr_iid}: {mr.title[:50]}...")
        return True
        
    except Exception as e:
        print(f"✗ Failed to download MR !{mr_iid}: {e}")
        return False


def download_recent_mrs(gl, project_id: int, count: int, output_dir: Path, 
                       state: str = 'merged') -> List[int]:
    """
    Download recent merge requests.
    
    Args:
        gl: GitLab connection
        project_id: GitLab project ID
        count: Number of MRs to download
        output_dir: Output directory
        state: MR state filter ('merged', 'opened', 'closed', 'all')
        
    Returns:
        List of successfully downloaded MR IIDs
    """
    try:
        project = gl.projects.get(project_id)
        
        # Get recent MRs
        mrs = project.mergerequests.list(
            state=state,
            order_by='updated_at',
            sort='desc',
            per_page=count
        )
        
        print(f"\nFound {len(mrs)} recent {state} MRs")
        print(f"Downloading to {output_dir}...")
        print("=" * 60)
        
        downloaded = []
        for mr in mrs:
            if download_mr(gl, project_id, mr.iid, output_dir):
                downloaded.append(mr.iid)
        
        print("=" * 60)
        print(f"\nSuccessfully downloaded {len(downloaded)}/{len(mrs)} MRs")
        
        return downloaded
        
    except Exception as e:
        print(f"✗ Failed to list MRs: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description='Download GitLab merge requests for local testing'
    )
    parser.add_argument(
        '--url',
        default=os.getenv('GITLAB_URL', 'https://gitlab.com'),
        help='GitLab URL (default: $GITLAB_URL or https://gitlab.com)'
    )
    parser.add_argument(
        '--token',
        default=os.getenv('GITLAB_TOKEN'),
        help='GitLab access token (default: $GITLAB_TOKEN)'
    )
    parser.add_argument(
        '--project-id',
        type=int,
        required=True,
        help='GitLab project ID'
    )
    parser.add_argument(
        '--mr-iid',
        type=int,
        help='Specific MR IID to download'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of recent MRs to download (default: 10)'
    )
    parser.add_argument(
        '--state',
        choices=['opened', 'closed', 'merged', 'all'],
        default='merged',
        help='MR state filter (default: merged)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('test_data/mrs'),
        help='Output directory (default: test_data/mrs)'
    )
    
    args = parser.parse_args()
    
    # Check token
    if not args.token:
        print("Error: GitLab token not provided")
        print("Set GITLAB_TOKEN environment variable or use --token")
        sys.exit(1)
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to GitLab
    print(f"Connecting to {args.url}...")
    try:
        gl = gitlab.Gitlab(args.url, private_token=args.token)
        gl.auth()
        print(f"✓ Authenticated as {gl.user.username}")
    except Exception as e:
        print(f"✗ Failed to connect to GitLab: {e}")
        sys.exit(1)
    
    # Download MR(s)
    if args.mr_iid:
        # Download specific MR
        success = download_mr(gl, args.project_id, args.mr_iid, args.output_dir)
        sys.exit(0 if success else 1)
    else:
        # Download recent MRs
        downloaded = download_recent_mrs(
            gl, args.project_id, args.count, args.output_dir, args.state
        )
        sys.exit(0 if downloaded else 1)


if __name__ == '__main__':
    main()
