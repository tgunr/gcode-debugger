#!/usr/bin/env python3

import os
import json
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime

class CodebaseIndexer:
    """
    A tool to index codebases and create collections in Qdrant vector database.
    Supports various file types and creates embeddings for semantic search.
    """

    def __init__(self, qdrant_url: str, api_key: str, collection_name: str):
        self.qdrant_url = qdrant_url.rstrip('/')
        self.api_key = api_key
        self.collection_name = collection_name
        self.headers = {
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }

        # File extensions to index
        self.supported_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
            '.sql', '.html', '.css', '.scss', '.less', '.xml', '.json',
            '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.md', '.rst',
            '.txt', '.sh', '.bat', '.ps1', '.dockerfile', '.makefile'
        }

        # Files/directories to exclude
        self.exclude_patterns = {
            '.git', '.svn', '.hg', '__pycache__', '.pytest_cache', 'node_modules',
            '.vscode', '.idea', '.DS_Store', '.venv', 'venv', 'env', 'build',
            'dist', 'target', '.ropeproject', '.mypy_cache', '.coverage',
            'coverage', 'htmlcov', '*.egg-info', '.tox', '.cache'
        }

    def should_exclude_path(self, path: Path) -> bool:
        """Check if a path should be excluded from indexing."""
        path_parts = path.parts
        for part in path_parts:
            if part in self.exclude_patterns or part.startswith('.'):
                # Allow some specific dotfiles
                if part not in {'.gitignore', '.dockerignore', '.env.example'}:
                    return True
        return False

    def get_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None

    def extract_file_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Extract metadata from file."""
        stats = file_path.stat()

        # Count lines and estimate complexity
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        # Basic complexity metrics
        complexity_keywords = ['if', 'for', 'while', 'class', 'def', 'function', 'try', 'catch']
        complexity_score = sum(
            line.lower().count(keyword)
            for line in non_empty_lines
            for keyword in complexity_keywords
        )

        return {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_extension': file_path.suffix,
            'directory': str(file_path.parent),
            'size_bytes': stats.st_size,
            'total_lines': len(lines),
            'non_empty_lines': len(non_empty_lines),
            'complexity_score': complexity_score,
            'last_modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'file_hash': hashlib.md5(content.encode('utf-8')).hexdigest()
        }

    def chunk_content(self, content: str, max_chunk_size: int = 1000) -> List[str]:
        """Split content into smaller chunks for better embedding."""
        if len(content) <= max_chunk_size:
            return [content]

        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def create_collection(self, vector_size: int = 384) -> bool:
        """Create a new Qdrant collection."""
        collection_config = {
            "vectors": {
                "size": vector_size,
                "distance": "Cosine"
            },
            "optimizers_config": {
                "default_segment_number": 2
            },
            "replication_factor": 1
        }

        url = f"{self.qdrant_url}/collections/{self.collection_name}"
        response = requests.put(url, headers=self.headers, json=collection_config)

        if response.status_code in [200, 201]:
            print(f"✓ Collection '{self.collection_name}' created successfully")
            return True
        elif response.status_code == 409:
            print(f"✓ Collection '{self.collection_name}' already exists")
            return True
        else:
            print(f"✗ Failed to create collection: {response.status_code} - {response.text}")
            return False

    def delete_collection(self) -> bool:
        """Delete the Qdrant collection."""
        url = f"{self.qdrant_url}/collections/{self.collection_name}"
        response = requests.delete(url, headers=self.headers)

        if response.status_code in [200, 404]:
            print(f"✓ Collection '{self.collection_name}' deleted")
            return True
        else:
            print(f"✗ Failed to delete collection: {response.status_code} - {response.text}")
            return False

    def get_collection_info(self) -> Optional[Dict]:
        """Get information about the collection."""
        url = f"{self.qdrant_url}/collections/{self.collection_name}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Collection not found or error: {response.status_code}")
            return None

    def index_directory(self, root_path: Path, max_files: Optional[int] = None) -> Dict[str, Any]:
        """Index all supported files in a directory."""
        indexed_files = []
        skipped_files = []
        total_chunks = 0

        print(f"Indexing directory: {root_path}")

        file_count = 0
        for file_path in root_path.rglob('*'):
            if max_files and file_count >= max_files:
                break

            # Skip if it's not a file
            if not file_path.is_file():
                continue

            # Skip if extension not supported
            if file_path.suffix.lower() not in self.supported_extensions:
                continue

            # Skip if path should be excluded
            if self.should_exclude_path(file_path):
                skipped_files.append(str(file_path))
                continue

            # Get file content
            content = self.get_file_content(file_path)
            if content is None:
                skipped_files.append(str(file_path))
                continue

            # Extract metadata
            metadata = self.extract_file_metadata(file_path, content)

            # Create chunks
            chunks = self.chunk_content(content)

            # Store file info
            indexed_files.append({
                'file_path': str(file_path),
                'metadata': metadata,
                'chunks': len(chunks),
                'content_preview': content[:200] + '...' if len(content) > 200 else content
            })

            total_chunks += len(chunks)
            file_count += 1

            if file_count % 10 == 0:
                print(f"Processed {file_count} files...")

        return {
            'indexed_files': indexed_files,
            'skipped_files': skipped_files,
            'total_files': len(indexed_files),
            'total_chunks': total_chunks,
            'statistics': {
                'by_extension': self._get_extension_stats(indexed_files),
                'by_directory': self._get_directory_stats(indexed_files),
                'complexity_distribution': self._get_complexity_stats(indexed_files)
            }
        }

    def _get_extension_stats(self, indexed_files: List[Dict]) -> Dict[str, int]:
        """Get statistics by file extension."""
        stats = {}
        for file_info in indexed_files:
            ext = file_info['metadata']['file_extension']
            stats[ext] = stats.get(ext, 0) + 1
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

    def _get_directory_stats(self, indexed_files: List[Dict]) -> Dict[str, int]:
        """Get statistics by directory."""
        stats = {}
        for file_info in indexed_files:
            directory = file_info['metadata']['directory']
            stats[directory] = stats.get(directory, 0) + 1
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True)[:20])  # Top 20

    def _get_complexity_stats(self, indexed_files: List[Dict]) -> Dict[str, int]:
        """Get complexity distribution."""
        complexity_ranges = {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0}

        for file_info in indexed_files:
            score = file_info['metadata']['complexity_score']
            if score == 0:
                complexity_ranges['low'] += 1
            elif score <= 10:
                complexity_ranges['medium'] += 1
            elif score <= 50:
                complexity_ranges['high'] += 1
            else:
                complexity_ranges['very_high'] += 1

        return complexity_ranges

    def save_index_report(self, index_data: Dict[str, Any], output_file: str = 'index_report.json'):
        """Save indexing report to file."""
        with open(output_file, 'w') as f:
            json.dump(index_data, f, indent=2, default=str)
        print(f"Index report saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Index codebase and create Qdrant collection')
    parser.add_argument('path', help='Path to directory to index')
    parser.add_argument('--qdrant-url', required=True, help='Qdrant server URL')
    parser.add_argument('--api-key', required=True, help='Qdrant API key')
    parser.add_argument('--collection', required=True, help='Collection name')
    parser.add_argument('--max-files', type=int, help='Maximum number of files to index')
    parser.add_argument('--recreate-collection', action='store_true',
                        help='Delete and recreate collection')
    parser.add_argument('--report-only', action='store_true',
                        help='Only generate index report, do not create collection')
    parser.add_argument('--output-report', default='index_report.json',
                        help='Output file for index report')

    args = parser.parse_args()

    # Initialize indexer
    indexer = CodebaseIndexer(args.qdrant_url, args.api_key, args.collection)

    # Check if path exists
    root_path = Path(args.path)
    if not root_path.exists():
        print(f"Error: Path {args.path} does not exist")
        return 1

    # Create or recreate collection
    if not args.report_only:
        if args.recreate_collection:
            indexer.delete_collection()

        if not indexer.create_collection():
            return 1

        # Show collection info
        info = indexer.get_collection_info()
        if info:
            print(f"Collection info: {json.dumps(info, indent=2)}")

    # Index the directory
    print("\nStarting indexing process...")
    index_data = indexer.index_directory(root_path, args.max_files)

    # Print summary
    print(f"\n=== Indexing Summary ===")
    print(f"Total files indexed: {index_data['total_files']}")
    print(f"Total chunks created: {index_data['total_chunks']}")
    print(f"Files skipped: {len(index_data['skipped_files'])}")

    print(f"\n=== By File Extension ===")
    for ext, count in index_data['statistics']['by_extension'].items():
        print(f"  {ext}: {count} files")

    print(f"\n=== Complexity Distribution ===")
    for level, count in index_data['statistics']['complexity_distribution'].items():
        print(f"  {level}: {count} files")

    # Save report
    indexer.save_index_report(index_data, args.output_report)

    if args.report_only:
        print(f"\nReport-only mode: Collection not created. See {args.output_report} for details.")
    else:
        print(f"\nIndexing complete! Collection '{args.collection}' is ready for use.")

    return 0

if __name__ == "__main__":
    exit(main())
