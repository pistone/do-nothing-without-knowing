"""
Setup script for auto-code-reviewer.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text() if readme_file.exists() else ''

setup(
    name='auto-code-reviewer',
    version='0.1.0',
    description='Intelligent code review agent using tree-sitter and semantic analysis',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/auto-code-reviewer',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=[
        'tree-sitter>=0.20.0',
        'tree-sitter-python>=0.20.0',
        'tree-sitter-cpp>=0.20.0',
        'tree-sitter-c>=0.20.0',
        'python-gitlab>=3.15.0',
        'requests>=2.31.0',
        'unidiff>=0.7.5',
        'pyyaml>=6.0',
        'click>=8.1.0',
        'numpy>=1.24.0',
        'pandas>=2.0.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
        ],
    },
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'review-mr=scripts.review_mr:main',
            'batch-review=scripts.batch_review:main',
            'download-mrs=scripts.download_mrs:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Quality Assurance',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
