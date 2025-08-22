#!/usr/bin/env python3

import os
import json
import hashlib
import argparse
import logging
import gc
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, Generator
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import time
import re
import tempfile
import mmap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DistanceMetric(Enum):
    """Qdrant distance metrics."""
    COSINE = "Cosine"
    EUCLIDEAN = "Euclid"
    DOT = "Dot"
    MANHATTAN = "Manhattan"

class QuantizationType(Enum):
    """Qdrant quantization types."""
    SCALAR = "scalar"
    PRODUCT = "product"
    BINARY = "binary"

@dataclass
class VectorParams:
    """Vector configuration parameters."""
    size: int
    distance: DistanceMetric
    hnsw_config: Optional[Dict] = None
    quantization_config: Optional[Dict] = None
    on_disk: Optional[bool] = None

@dataclass
class CollectionConfig:
    """Complete collection configuration."""
    vectors: Union[VectorParams, Dict[str, VectorParams]]
    shard_number: Optional[int] = None
    replication_factor: Optional[int] = None
    write_consistency_factor: Optional[int] = None
    on_disk_payload: Optional[bool] = None
    hnsw_config: Optional[Dict] = None
    wal_config: Optional[Dict] = None
    optimizers_config: Optional[Dict] = None
    init_from: Optional[Dict] = None
    quantization_config: Optional[Dict] = None

@dataclass
class FileMetadata:
    """Metadata for indexed files."""
    file_path: str
    size_bytes: int
    language: str
    last_modified: str
    file_hash: str
    imports: List[str]
    functions: List[str]
    classes: List[str]
    complexity_score: float
    keywords: List[str]

@dataclass
class CodeChunk:
    """Represents a code chunk with metadata."""
    content: str
    chunk_index: int
    start_line: int
    end_line: int
    file_path: str
    language: str
    complexity_score: float
    keywords: List[str]

class MemoryEfficientIndexer:
    """Memory-efficient codebase indexer with batch processing."""

    def __init__(self, qdrant_url: str = "http://localhost:6333", batch_size: int = 50, max_file_size_mb: int = 10):
        self.qdrant_url = qdrant_url
        self.batch_size = batch_size
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

        # Supported file extensions and their languages
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.m': 'matlab',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.xml': 'xml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'conf',
            '.sh': 'shell',
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.fish': 'fish',
            '.ps1': 'powershell',
            '.bat': 'batch',
            '.cmd': 'batch',
            '.dockerfile': 'dockerfile',
            '.md': 'markdown',
            '.txt': 'text',
            '.rst': 'restructuredtext',
            '.tex': 'latex',
            '.vim': 'vim',
            '.lua': 'lua',
            '.pl': 'perl',
            '.pm': 'perl'
        }

        # Language-specific patterns for parsing
        self.language_patterns = {
            'python': {
                'function': r'^\s*def\s+(\w+)\s*\(',
                'class': r'^\s*class\s+(\w+)\s*[:\(]',
                'import': r'^\s*(?:from\s+\S+\s+)?import\s+(.+)',
                'keywords': ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with', 'async', 'await']
            },
            'javascript': {
                'function': r'(?:function\s+(\w+)|(\w+)\s*[:=]\s*function|\s*(\w+)\s*\([^)]*\)\s*=>)',
                'class': r'^\s*class\s+(\w+)',
                'import': r'(?:import\s+.*\s+from\s+["\']([^"\']+)["\']|import\s+["\']([^"\']+)["\'])',
                'keywords': ['function', 'class', 'import', 'export', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'try', 'catch', 'finally', 'async', 'await']
            },
            'java': {
                'function': r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(',
                'class': r'(?:public|private|protected)?\s*(?:abstract)?\s*class\s+(\w+)',
                'import': r'import\s+(?:static\s+)?([^;]+);',
                'keywords': ['class', 'interface', 'public', 'private', 'protected', 'static', 'final', 'abstract', 'extends', 'implements', 'import', 'package']
            }
        }

    def get_file_iterator(self, root_path: Path) -> Generator[Path, None, None]:
        """Memory-efficient file iterator."""
        for file_path in root_path.rglob('*'):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in self.supported_extensions:
                continue

            # Skip files that are too large
            try:
                if file_path.stat().st_size > self.max_file_size_bytes:
                    logger.warning(f"Skipping large file: {file_path} ({file_path.stat().st_size / 1024 / 1024:.1f}MB)")
                    continue
            except OSError:
                continue

            yield file_path

    def read_file_safely(self, file_path: Path) -> Optional[str]:
        """Safely read file with memory mapping for large files."""
        try:
            file_size = file_path.stat().st_size

            # For small files, read normally
            if file_size < 1024 * 1024:  # 1MB
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()

            # For larger files, use memory mapping
            with open(file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    content = mm.read().decode('utf-8', errors='ignore')
                    return content

        except (IOError, OSError, UnicodeDecodeError) as e:
            logger.warning(f"Could not read file {file_path}: {e}")
            return None

    def analyze_code_structure(self, content: str, language: str) -> Dict[str, Any]:
        """Analyze code structure with minimal memory usage."""
        if language not in self.language_patterns:
            return {'functions': [], 'classes': [], 'imports': [], 'keywords': []}

        patterns = self.language_patterns[language]
        structure = {
            'functions': [],
            'classes': [],
            'imports': [],
            'keywords': []
        }

        lines = content.split('\n')

        # Process line by line to avoid keeping large structures in memory
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue

            # Extract functions
            if 'function' in patterns:
                func_match = re.search(patterns['function'], line)
                if func_match:
                    func_name = next(g for g in func_match.groups() if g)
                    if func_name and len(structure['functions']) < 100:  # Limit to prevent memory issues
                        structure['functions'].append(func_name)

            # Extract classes
            if 'class' in patterns:
                class_match = re.search(patterns['class'], line)
                if class_match and len(structure['classes']) < 50:
                    structure['classes'].append(class_match.group(1))

            # Extract imports
            if 'import' in patterns:
                import_match = re.search(patterns['import'], line)
                if import_match and len(structure['imports']) < 100:
                    import_name = next(g for g in import_match.groups() if g)
                    if import_name:
                        structure['imports'].append(import_name.strip())

        # Extract keywords
        keywords_set = set()
        for keyword in patterns.get('keywords', []):
            if keyword in content and len(keywords_set) < 50:
                keywords_set.add(keyword)

        structure['keywords'] = list(keywords_set)
        return structure

    def calculate_complexity_score(self, content: str, language: str, structure: Dict) -> float:
        """Calculate a simple complexity score."""
        lines = len(content.split('\n'))
        functions = len(structure.get('functions', []))
        classes = len(structure.get('classes', []))

        # Simple heuristic
        base_score = min(lines / 100, 5.0)  # Cap at 5.0
        function_bonus = min(functions * 0.1, 2.0)
        class_bonus = min(classes * 0.2, 2.0)

        return min(base_score + function_bonus + class_bonus, 10.0)

    def extract_file_metadata(self, file_path: Path, content: str, root_path: Path) -> FileMetadata:
        """Extract metadata from a file."""
        stats = file_path.stat()
        language = self.supported_extensions.get(file_path.suffix.lower(), 'unknown')

        structure = self.analyze_code_structure(content, language)
        complexity_score = self.calculate_complexity_score(content, language, structure)

        return FileMetadata(
            file_path=str(file_path.relative_to(root_path)),
            size_bytes=stats.st_size,
            language=language,
            last_modified=datetime.fromtimestamp(stats.st_mtime).isoformat(),
            file_hash=hashlib.md5(content.encode('utf-8')).hexdigest(),
            imports=structure['imports'],
            functions=structure['functions'],
            classes=structure['classes'],
            complexity_score=complexity_score,
            keywords=structure['keywords']
        )

    def create_smart_chunks(self, content: str, file_metadata: FileMetadata, max_chunk_size: int = 1000) -> List[CodeChunk]:
        """Create intelligent code chunks with minimal memory usage."""
        if len(content) <= max_chunk_size:
            return [CodeChunk(
                content=content,
                chunk_index=0,
                start_line=1,
                end_line=len(content.split('\n')),
                file_path=file_metadata.file_path,
                language=file_metadata.language,
                complexity_score=file_metadata.complexity_score,
                keywords=file_metadata.keywords[:10]  # Limit keywords
            )]

        # Simple line-based chunking for memory efficiency
        lines = content.split('\n')
        chunks = []
        chunk_index = 0

        i = 0
        while i < len(lines):
            current_chunk_lines = []
            current_size = 0
            start_line = i + 1

            # Build chunk up to max size
            while i < len(lines) and current_size < max_chunk_size:
                line = lines[i]
                current_chunk_lines.append(line)
                current_size += len(line) + 1
                i += 1

            chunk_content = '\n'.join(current_chunk_lines)
            if chunk_content.strip():
                chunks.append(CodeChunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_line=start_line,
                    end_line=start_line + len(current_chunk_lines) - 1,
                    file_path=file_metadata.file_path,
                    language=file_metadata.language,
                    complexity_score=min(file_metadata.complexity_score, 5.0),
                    keywords=file_metadata.keywords[:5]  # Limit keywords per chunk
                ))
                chunk_index += 1

                # Clear memory
                del current_chunk_lines

        return chunks

    def process_file_batch(self, file_paths: List[Path], root_path: Path) -> Tuple[List[Dict], List[str]]:
        """Process a batch of files efficiently."""
        indexed_files = []
        skipped_files = []

        for file_path in file_paths:
            try:
                content = self.read_file_safely(file_path)
                if content is None:
                    skipped_files.append(str(file_path))
                    continue

                metadata = self.extract_file_metadata(file_path, content, root_path)
                chunks = self.create_smart_chunks(content, metadata)

                # Create minimal file info to save memory
                file_info = {
                    'file_path': str(file_path.relative_to(root_path)),
                    'size_bytes': metadata.size_bytes,
                    'language': metadata.language,
                    'chunks': len(chunks),
                    'complexity_score': metadata.complexity_score,
                    'function_count': len(metadata.functions),
                    'class_count': len(metadata.classes),
                    'import_count': len(metadata.imports)
                }

                indexed_files.append(file_info)

                # Clear memory
                del content
                del metadata
                del chunks

            except Exception as e:
                logger.warning(f"Error processing file {file_path}: {e}")
                skipped_files.append(str(file_path))

        # Force garbage collection
        gc.collect()
        return indexed_files, skipped_files

    def index_directory_batched(self, root_path: Path, max_files: Optional[int] = None) -> Dict[str, Any]:
        """Index directory in batches to manage memory usage."""
        all_indexed_files = []
        all_skipped_files = []
        total_files_processed = 0

        logger.info(f"Starting memory-efficient indexing of directory: {root_path}")
        logger.info(f"Batch size: {self.batch_size}, Max file size: {self.max_file_size_bytes / 1024 / 1024:.1f}MB")

        # Create batches
        batch = []
        for file_path in self.get_file_iterator(root_path):
            batch.append(file_path)

            if len(batch) >= self.batch_size:
                indexed_files, skipped_files = self.process_file_batch(batch, root_path)
                all_indexed_files.extend(indexed_files)
                all_skipped_files.extend(skipped_files)
                total_files_processed += len(batch)

                logger.info(f"Processed batch of {len(batch)} files. Total processed: {total_files_processed}")

                batch = []

                if max_files and total_files_processed >= max_files:
                    break

        # Process remaining files in the last batch
        if batch and (not max_files or total_files_processed < max_files):
            remaining_files = batch
            if max_files:
                remaining_files = batch[:max_files - total_files_processed]

            indexed_files, skipped_files = self.process_file_batch(remaining_files, root_path)
            all_indexed_files.extend(indexed_files)
            all_skipped_files.extend(skipped_files)
            total_files_processed += len(remaining_files)

        # Generate statistics
        statistics = self._generate_statistics(all_indexed_files)

        logger.info(f"Indexing complete. Processed: {len(all_indexed_files)}, Skipped: {len(all_skipped_files)}")

        return {
            'indexed_files': all_indexed_files,
            'skipped_files': all_skipped_files,
            'total_files': len(all_indexed_files),
            'total_files_processed': total_files_processed,
            'statistics': statistics,
            'indexing_timestamp': datetime.now().isoformat(),
            'project_root': str(root_path),
            'batch_size': self.batch_size,
            'max_file_size_mb': self.max_file_size_bytes / 1024 / 1024
        }

    def _generate_statistics(self, indexed_files: List[Dict]) -> Dict[str, Any]:
        """Generate statistics with memory efficiency in mind."""
        stats = {
            'by_language': {},
            'by_extension': {},
            'size_distribution': {'small': 0, 'medium': 0, 'large': 0},
            'complexity_distribution': {'low': 0, 'medium': 0, 'high': 0},
            'total_functions': 0,
            'total_classes': 0,
            'total_imports': 0
        }

        for file_info in indexed_files:
            # Language statistics
            lang = file_info.get('language', 'unknown')
            stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1

            # Size distribution
            size = file_info.get('size_bytes', 0)
            if size < 1024:
                stats['size_distribution']['small'] += 1
            elif size < 10240:
                stats['size_distribution']['medium'] += 1
            else:
                stats['size_distribution']['large'] += 1

            # Complexity distribution
            complexity = file_info.get('complexity_score', 0)
            if complexity < 2.0:
                stats['complexity_distribution']['low'] += 1
            elif complexity < 5.0:
                stats['complexity_distribution']['medium'] += 1
            else:
                stats['complexity_distribution']['high'] += 1

            # Aggregate counts
            stats['total_functions'] += file_info.get('function_count', 0)
            stats['total_classes'] += file_info.get('class_count', 0)
            stats['total_imports'] += file_info.get('import_count', 0)

        return stats

    def save_index_report(self, index_data: Dict[str, Any], output_file: str = 'memory_efficient_index_report.json'):
        """Save indexing report to file."""
        try:
            with open(output_file, 'w') as f:
                json.dump(index_data, f, indent=2, default=str)
            logger.info(f"Index report saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving index report: {e}")

    def create_collection_schema(self, collection_name: str, vector_size: int = 384,
                                distance_metric: DistanceMetric = DistanceMetric.COSINE,
                                enable_quantization: bool = True) -> Dict[str, Any]:
        """Create a memory-optimized collection schema."""
        hnsw_config = {
            "m": 16,
            "ef_construct": 100,
            "full_scan_threshold": 10000,
            "max_indexing_threads": 2,  # Limit threads to reduce memory usage
            "on_disk": True,  # Store on disk to save memory
            "payload_m": 16
        }

        quantization_config = None
        if enable_quantization:
            quantization_config = {
                "scalar": {
                    "type": "int8",
                    "quantile": 0.99,
                    "always_ram": False  # Allow storing quantized vectors on disk
                }
            }

        vector_config = {
            "size": vector_size,
            "distance": distance_metric.value,
            "hnsw_config": hnsw_config,
            "quantization_config": quantization_config,
            "on_disk": True  # Store vectors on disk
        }

        collection_config = {
            "vectors": vector_config,
            "shard_number": 1,  # Single shard for simplicity
            "replication_factor": 1,
            "on_disk_payload": True,  # Store payload on disk
            "optimizers_config": {
                "deleted_threshold": 0.2,
                "vacuum_min_vector_number": 1000,
                "default_segment_number": 2,  # Fewer segments to reduce memory
                "max_segment_size": 200000,
                "memmap_threshold": 50000,
                "indexing_threshold": 20000,
                "flush_interval_sec": 30,
                "max_optimization_threads": 1  # Limit optimization threads
            }
        }

        return collection_config

    def create_collection(self, collection_name: str) -> bool:
        """Create a memory-optimized collection."""
        try:
            schema = self.create_collection_schema(collection_name)

            response = requests.put(
                f"{self.qdrant_url}/collections/{collection_name}",
                json=schema,
                headers={"Content-Type": "application/json"},
                timeout=30
            )

            if response.status_code in [200, 201]:
                logger.info(f"Collection '{collection_name}' created successfully")
                return True
            else:
                logger.error(f"Failed to create collection: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False

def main():
    """Main entry point for the memory-efficient indexer."""
    parser = argparse.ArgumentParser(description='Memory-Efficient Codebase Indexer')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Index command
    index_parser = subparsers.add_parser('index', help='Index a directory')
    index_parser.add_argument('directory', help='Directory to index')
    index_parser.add_argument('--collection', required=True, help='Collection name')
    index_parser.add_argument('--max-files', type=int, help='Maximum number of files to index')
    index_parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing')
    index_parser.add_argument('--max-file-size', type=int, default=10, help='Maximum file size in MB')
    index_parser.add_argument('--output-report', default='memory_efficient_index_report.json', help='Output report file')
    index_parser.add_argument('--qdrant-url', default='http://localhost:6333', help='Qdrant URL')

    # Create collection command
    create_parser = subparsers.add_parser('create-collection', help='Create a collection')
    create_parser.add_argument('collection_name', help='Collection name')
    create_parser.add_argument('--qdrant-url', default='http://localhost:6333', help='Qdrant URL')

    args = parser.parse_args()

    if args.command == 'index':
        indexer = MemoryEfficientIndexer(
            qdrant_url=args.qdrant_url,
            batch_size=args.batch_size,
            max_file_size_mb=args.max_file_size
        )

        root_path = Path(args.directory).resolve()
        if not root_path.exists():
            logger.error(f"Directory does not exist: {root_path}")
            return 1

        logger.info(f"Starting memory-efficient indexing of: {root_path}")

        index_data = indexer.index_directory_batched(root_path, args.max_files)
        indexer.save_index_report(index_data, args.output_report)

        logger.info(f"=== Indexing Summary ===")
        logger.info(f"Total files indexed: {index_data['total_files']}")
        logger.info(f"Files skipped: {len(index_data['skipped_files'])}")
        logger.info(f"Batch size used: {index_data['batch_size']}")
        logger.info(f"Max file size: {index_data['max_file_size_mb']}MB")

    elif args.command == 'create-collection':
        indexer = MemoryEfficientIndexer(qdrant_url=args.qdrant_url)
        success = indexer.create_collection(args.collection_name)
        return 0 if success else 1

    else:
        parser.print_help()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
