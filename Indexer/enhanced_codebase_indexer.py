#!/usr/bin/env python3

import os
import json
import hashlib
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import time
import re

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
    quantization_config: Optional[Dict] = None
    sparse_vectors: Optional[Dict[str, Dict]] = None
    strict_mode_config: Optional[Dict] = None

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

@dataclass
class FileMetadata:
    """Enhanced file metadata."""
    file_path: str
    file_name: str
    file_extension: str
    directory: str
    size_bytes: int
    total_lines: int
    non_empty_lines: int
    complexity_score: float
    language: str
    last_modified: str
    file_hash: str
    imports: List[str]
    functions: List[str]
    classes: List[str]
    keywords: List[str]
    project_relative_path: str

class EnhancedCodebaseIndexer:
    """
    Enhanced codebase indexer with sophisticated Qdrant collection management
    and advanced code analysis capabilities.
    """

    def __init__(self, qdrant_url: str, api_key: str):
        self.qdrant_url = qdrant_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'api-key': self.api_key
        }

        # Enhanced file extensions with language mapping
        self.language_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
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
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'css',
            '.less': 'css',
            '.xml': 'xml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'config',
            '.conf': 'config',
            '.md': 'markdown',
            '.rst': 'restructuredtext',
            '.txt': 'text',
            '.sh': 'shell',
            '.bat': 'batch',
            '.ps1': 'powershell',
            '.dockerfile': 'dockerfile',
            '.makefile': 'makefile'
        }

        # Language-specific patterns for analysis
        self.language_patterns = {
            'python': {
                'import': r'^\s*(?:from\s+\S+\s+)?import\s+(.+)',
                'function': r'^\s*def\s+(\w+)\s*\(',
                'class': r'^\s*class\s+(\w+)\s*[:\(]',
                'keywords': ['def', 'class', 'if', 'for', 'while', 'try', 'except', 'with', 'async', 'await']
            },
            'javascript': {
                'import': r'^\s*import\s+.+\s+from\s+["\'](.+)["\']',
                'function': r'^\s*(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:\([^)]*\)\s*=>|function))',
                'class': r'^\s*class\s+(\w+)',
                'keywords': ['function', 'class', 'if', 'for', 'while', 'try', 'catch', 'async', 'await', 'const', 'let']
            },
            'typescript': {
                'import': r'^\s*import\s+.+\s+from\s+["\'](.+)["\']',
                'function': r'^\s*(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:\([^)]*\)\s*=>|function))',
                'class': r'^\s*(?:export\s+)?class\s+(\w+)',
                'keywords': ['function', 'class', 'interface', 'type', 'if', 'for', 'while', 'try', 'catch', 'async', 'await']
            },
            'java': {
                'import': r'^\s*import\s+(.+);',
                'function': r'^\s*(?:public|private|protected)?\s*(?:static\s+)?(?:\w+\s+)+(\w+)\s*\(',
                'class': r'^\s*(?:public\s+)?class\s+(\w+)',
                'keywords': ['class', 'interface', 'public', 'private', 'static', 'if', 'for', 'while', 'try', 'catch']
            }
        }

        # Exclude patterns
        self.exclude_patterns = {
            '.git', '.svn', '.hg', '__pycache__', '.pytest_cache', 'node_modules',
            '.vscode', '.idea', '.DS_Store', '.venv', 'venv', 'env', 'build',
            'dist', 'target', '.ropeproject', '.mypy_cache', '.coverage',
            'coverage', 'htmlcov', '*.egg-info', '.tox', '.cache', 'logs',
            '.next', '.nuxt', 'vendor', 'bower_components', 'jspm_packages'
        }

    def create_collection_schema(self,
                                collection_name: str,
                                vector_size: int = 384,
                                distance_metric: DistanceMetric = DistanceMetric.COSINE,
                                enable_quantization: bool = False,
                                quantization_type: QuantizationType = QuantizationType.SCALAR,
                                enable_sparse_vectors: bool = False,
                                replication_factor: int = 1,
                                shard_number: Optional[int] = None,
                                optimizers_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a comprehensive collection schema with advanced configuration.

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of dense vectors (default: 384 for sentence-transformers)
            distance_metric: Distance metric for vector comparison
            enable_quantization: Whether to enable vector quantization
            quantization_type: Type of quantization to use
            enable_sparse_vectors: Whether to enable sparse vectors for keyword search
            replication_factor: Number of replicas for high availability
            shard_number: Number of shards (auto-calculated if None)
            optimizers_config: Custom optimizer configuration
        """

        # Base vector configuration
        vectors_config = {
            "size": vector_size,
            "distance": distance_metric.value
        }

        # HNSW configuration for optimal search performance
        hnsw_config = {
            "m": 16,  # Number of bi-directional links for each node during construction
            "ef_construct": 100,  # Size of dynamic list during construction
            "full_scan_threshold": 10000,  # Threshold for full scan vs HNSW search
            "max_indexing_threads": 0,  # 0 means use all available threads
            "on_disk": False,  # Keep HNSW index in memory for better performance
            "payload_m": 16  # Number of connections for payload-aware index
        }

        # Quantization configuration for memory optimization
        quantization_config = None
        if enable_quantization:
            if quantization_type == QuantizationType.SCALAR:
                quantization_config = {
                    "scalar": {
                        "type": "int8",
                        "quantile": 0.99,
                        "always_ram": True
                    }
                }
            elif quantization_type == QuantizationType.PRODUCT:
                quantization_config = {
                    "product": {
                        "compression": "x16",
                        "always_ram": True
                    }
                }
            elif quantization_type == QuantizationType.BINARY:
                quantization_config = {
                    "binary": {
                        "always_ram": True
                    }
                }

        # Sparse vectors configuration for hybrid search
        sparse_vectors_config = None
        if enable_sparse_vectors:
            sparse_vectors_config = {
                "text": {
                    "index": {
                        "on_disk": False,
                        "full_scan_threshold": 10000
                    }
                }
            }

        # Optimizers configuration
        if optimizers_config is None:
            optimizers_config = {
                "deleted_threshold": 0.2,
                "vacuum_min_vector_number": 1000,
                "default_segment_number": 0,  # Auto-determine based on RAM
                "max_segment_size": None,  # No limit
                "memmap_threshold": None,  # Auto-determine
                "indexing_threshold": 20000,
                "flush_interval_sec": 5,
                "max_optimization_threads": 1
            }

        # WAL configuration for durability
        wal_config = {
            "wal_capacity_mb": 32,
            "wal_segments_ahead": 0
        }

        # Build complete collection configuration
        collection_config = {
            "vectors": vectors_config,
            "hnsw_config": hnsw_config,
            "optimizers_config": optimizers_config,
            "wal_config": wal_config,
            "replication_factor": replication_factor,
            "write_consistency_factor": min(replication_factor, 1),
            "on_disk_payload": True,  # Store payloads on disk to save RAM
        }

        # Add optional configurations
        if shard_number is not None:
            collection_config["shard_number"] = shard_number

        if quantization_config:
            collection_config["quantization_config"] = quantization_config

        if sparse_vectors_config:
            collection_config["sparse_vectors"] = sparse_vectors_config

        return collection_config

    def create_collection(self, collection_name: str, config: Dict[str, Any]) -> bool:
        """Create a collection with the given configuration."""
        url = f"{self.qdrant_url}/collections/{collection_name}"

        logger.info(f"Creating collection '{collection_name}' with configuration:")
        logger.info(json.dumps(config, indent=2))

        response = requests.put(url, headers=self.headers, json=config)

        if response.status_code in [200, 201]:
            logger.info(f"✓ Collection '{collection_name}' created successfully")
            return True
        elif response.status_code == 409:
            logger.info(f"✓ Collection '{collection_name}' already exists")
            return True
        else:
            logger.error(f"✗ Failed to create collection: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        url = f"{self.qdrant_url}/collections/{collection_name}"
        response = requests.delete(url, headers=self.headers)

        if response.status_code in [200, 404]:
            logger.info(f"✓ Collection '{collection_name}' deleted")
            return True
        else:
            logger.error(f"✗ Failed to delete collection: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

    def get_collection_info(self, collection_name: str) -> Optional[Dict]:
        """Get detailed collection information."""
        url = f"{self.qdrant_url}/collections/{collection_name}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get collection info: {response.status_code}")
            return None

    def list_collections(self) -> List[Dict]:
        """List all collections."""
        url = f"{self.qdrant_url}/collections"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            result = response.json()
            return result.get('result', {}).get('collections', [])
        else:
            logger.error(f"Failed to list collections: {response.status_code}")
            return []

    def should_exclude_path(self, path: Path) -> bool:
        """Check if a path should be excluded."""
        path_parts = path.parts
        for part in path_parts:
            if part in self.exclude_patterns or (part.startswith('.') and part not in {'.gitignore', '.dockerignore', '.env.example'}):
                return True
        return False

    def detect_language(self, file_path: Path) -> str:
        """Detect the programming language of a file."""
        extension = file_path.suffix.lower()
        return self.language_extensions.get(extension, 'text')

    def analyze_code_structure(self, content: str, language: str) -> Dict[str, List[str]]:
        """Analyze code structure to extract imports, functions, and classes."""
        analysis = {
            'imports': [],
            'functions': [],
            'classes': [],
            'keywords': []
        }

        if language not in self.language_patterns:
            return analysis

        patterns = self.language_patterns[language]
        lines = content.split('\n')

        for line in lines:
            # Extract imports
            if 'import' in patterns:
                import_match = re.search(patterns['import'], line)
                if import_match:
                    analysis['imports'].append(import_match.group(1).strip())

            # Extract functions
            if 'function' in patterns:
                func_match = re.search(patterns['function'], line)
                if func_match:
                    # Handle multiple capture groups
                    for group in func_match.groups():
                        if group:
                            analysis['functions'].append(group.strip())
                            break

            # Extract classes
            if 'class' in patterns:
                class_match = re.search(patterns['class'], line)
                if class_match:
                    analysis['classes'].append(class_match.group(1).strip())

        # Count keywords for complexity analysis
        content_lower = content.lower()
        for keyword in patterns.get('keywords', []):
            count = content_lower.count(keyword)
            analysis['keywords'].extend([keyword] * count)

        return analysis

    def calculate_complexity_score(self, content: str, language: str, structure: Dict[str, List[str]]) -> float:
        """Calculate a complexity score for the code."""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        # Base complexity from line count
        base_score = len(non_empty_lines) * 0.1

        # Add complexity from code structures
        structure_score = (
            len(structure['functions']) * 2.0 +
            len(structure['classes']) * 3.0 +
            len(structure['keywords']) * 0.5
        )

        # Language-specific multipliers
        language_multipliers = {
            'python': 1.0,
            'javascript': 1.1,
            'typescript': 1.2,
            'java': 1.3,
            'cpp': 1.5,
            'c': 1.4
        }

        multiplier = language_multipliers.get(language, 1.0)

        return (base_score + structure_score) * multiplier

    def extract_file_metadata(self, file_path: Path, content: str, project_root: Path) -> FileMetadata:
        """Extract comprehensive metadata from a file."""
        stats = file_path.stat()
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        language = self.detect_language(file_path)
        structure = self.analyze_code_structure(content, language)
        complexity_score = self.calculate_complexity_score(content, language, structure)

        # Calculate relative path from project root
        try:
            relative_path = file_path.relative_to(project_root)
        except ValueError:
            relative_path = file_path

        return FileMetadata(
            file_path=str(file_path),
            file_name=file_path.name,
            file_extension=file_path.suffix,
            directory=str(file_path.parent),
            size_bytes=stats.st_size,
            total_lines=len(lines),
            non_empty_lines=len(non_empty_lines),
            complexity_score=complexity_score,
            language=language,
            last_modified=datetime.fromtimestamp(stats.st_mtime).isoformat(),
            file_hash=hashlib.md5(content.encode('utf-8')).hexdigest(),
            imports=structure['imports'],
            functions=structure['functions'],
            classes=structure['classes'],
            keywords=list(set(structure['keywords'])),  # Remove duplicates
            project_relative_path=str(relative_path)
        )

    def create_smart_chunks(self, content: str, file_metadata: FileMetadata,
                          max_chunk_size: int = 1000, overlap: int = 100) -> List[CodeChunk]:
        """Create intelligent code chunks with context preservation."""
        lines = content.split('\n')
        chunks = []

        if len(content) <= max_chunk_size:
            return [CodeChunk(
                content=content,
                chunk_index=0,
                start_line=1,
                end_line=len(lines),
                file_path=file_metadata.file_path,
                language=file_metadata.language,
                complexity_score=file_metadata.complexity_score,
                keywords=file_metadata.keywords
            )]

        # Try to chunk by logical boundaries for code files
        if file_metadata.language in ['python', 'javascript', 'typescript', 'java', 'cpp', 'c']:
            chunks = self._chunk_by_functions_classes(content, file_metadata, max_chunk_size)

        # Fall back to line-based chunking if logical chunking fails
        if not chunks:
            chunks = self._chunk_by_lines(content, file_metadata, max_chunk_size, overlap)

        return chunks

    def _chunk_by_functions_classes(self, content: str, file_metadata: FileMetadata,
                                  max_chunk_size: int) -> List[CodeChunk]:
        """Chunk code by function and class boundaries."""
        lines = content.split('\n')
        chunks = []
        current_chunk_lines = []
        current_start_line = 1
        chunk_index = 0

        language = file_metadata.language
        if language not in self.language_patterns:
            return []

        patterns = self.language_patterns[language]
        function_pattern = patterns.get('function', '')
        class_pattern = patterns.get('class', '')

        i = 0
        while i < len(lines):
            line = lines[i]
            current_chunk_lines.append(line)

            # Check if we hit a function or class boundary
            is_boundary = False
            if function_pattern and re.search(function_pattern, line):
                is_boundary = True
            elif class_pattern and re.search(class_pattern, line):
                is_boundary = True

            # If we hit a boundary or max size, create a chunk
            current_size = len('\n'.join(current_chunk_lines))
            if (is_boundary and len(current_chunk_lines) > 1) or current_size > max_chunk_size:
                if is_boundary and len(current_chunk_lines) > 1:
                    # Don't include the boundary line in current chunk
                    chunk_content = '\n'.join(current_chunk_lines[:-1])
                    end_line = current_start_line + len(current_chunk_lines) - 2
                else:
                    chunk_content = '\n'.join(current_chunk_lines)
                    end_line = current_start_line + len(current_chunk_lines) - 1

                if chunk_content.strip():  # Only add non-empty chunks
                    chunks.append(CodeChunk(
                        content=chunk_content,
                        chunk_index=chunk_index,
                        start_line=current_start_line,
                        end_line=end_line,
                        file_path=file_metadata.file_path,
                        language=file_metadata.language,
                        complexity_score=self._calculate_chunk_complexity(chunk_content, file_metadata.language),
                        keywords=self._extract_chunk_keywords(chunk_content, file_metadata.language)
                    ))
                    chunk_index += 1

                # Start new chunk
                if is_boundary and len(current_chunk_lines) > 1:
                    current_chunk_lines = [line]  # Start with boundary line
                    current_start_line = i + 1
                else:
                    current_chunk_lines = []
                    current_start_line = i + 1

            i += 1

        # Add final chunk if there's remaining content
        if current_chunk_lines and '\n'.join(current_chunk_lines).strip():
            chunk_content = '\n'.join(current_chunk_lines)
            chunks.append(CodeChunk(
                content=chunk_content,
                chunk_index=chunk_index,
                start_line=current_start_line,
                end_line=current_start_line + len(current_chunk_lines) - 1,
                file_path=file_metadata.file_path,
                language=file_metadata.language,
                complexity_score=self._calculate_chunk_complexity(chunk_content, file_metadata.language),
                keywords=self._extract_chunk_keywords(chunk_content, file_metadata.language)
            ))

        return chunks

    def _chunk_by_lines(self, content: str, file_metadata: FileMetadata,
                       max_chunk_size: int, overlap: int) -> List[CodeChunk]:
        """Chunk content by lines with overlap."""
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
                current_size += len(line) + 1  # +1 for newline
                i += 1

            chunk_content = '\n'.join(current_chunk_lines)
            if chunk_content.strip():  # Only add non-empty chunks
                chunks.append(CodeChunk(
                    content=chunk_content,
                    chunk_index=chunk_index,
                    start_line=start_line,
                    end_line=start_line + len(current_chunk_lines) - 1,
                    file_path=file_metadata.file_path,
                    language=file_metadata.language,
                    complexity_score=self._calculate_chunk_complexity(chunk_content, file_metadata.language),
                    keywords=self._extract_chunk_keywords(chunk_content, file_metadata.language)
                ))
                chunk_index += 1

            # Apply overlap for next chunk
            if overlap > 0 and i < len(lines):
                overlap_lines = min(overlap, len(current_chunk_lines))
                i -= overlap_lines

        return chunks

    def _calculate_chunk_complexity(self, content: str, language: str) -> float:
        """Calculate complexity score for a chunk."""
        structure = self.analyze_code_structure(content, language)
        return self.calculate_complexity_score(content, language, structure)

    def _extract_chunk_keywords(self, content: str, language: str) -> List[str]:
        """Extract keywords from a chunk."""
        structure = self.analyze_code_structure(content, language)
        return list(set(structure['keywords']))

    def get_file_content(self, file_path: Path) -> Optional[str]:
        """Read file content safely."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None

    def index_directory(self, root_path: Path, max_files: Optional[int] = None) -> Dict[str, Any]:
        """Index all supported files in a directory with enhanced analysis."""
        indexed_files = []
        skipped_files = []
        total_chunks = 0
        total_points = 0

        logger.info(f"Starting enhanced indexing of directory: {root_path}")

        file_count = 0
        for file_path in root_path.rglob('*'):
            if max_files and file_count >= max_files:
                break

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in self.language_extensions:
                continue

            if self.should_exclude_path(file_path):
                skipped_files.append(str(file_path))
                continue

            content = self.get_file_content(file_path)
            if content is None:
                skipped_files.append(str(file_path))
                continue

            # Extract comprehensive metadata
            metadata = self.extract_file_metadata(file_path, content, root_path)

            # Create intelligent chunks
            chunks = self.create_smart_chunks(content, metadata)

            # Store file info with enhanced metadata
            file_info = {
                'file_path': str(file_path),
                'metadata': asdict(metadata),
                'chunks': len(chunks),
                'content_preview': content[:300] + '...' if len(content) > 300 else content,
                'chunk_details': [
                    {
                        'chunk_index': chunk.chunk_index,
                        'start_line': chunk.start_line,
                        'end_line': chunk.end_line,
                        'complexity_score': chunk.complexity_score,
                        'keyword_count': len(chunk.keywords),
                        'content_length': len(chunk.content)
                    }
                    for chunk in chunks
                ]
            }

            indexed_files.append(file_info)
            total_chunks += len(chunks)
            total_points += len(chunks)  # Each chunk becomes a point
            file_count += 1

            if file_count % 10 == 0:
                logger.info(f"Processed {file_count} files, created {total_chunks} chunks...")

        # Generate comprehensive statistics
        statistics = self._generate_enhanced_statistics(indexed_files)

        return {
            'indexed_files': indexed_files,
            'skipped_files': skipped_files,
            'total_files': len(indexed_files),
            'total_chunks': total_chunks,
            'total_points': total_points,
            'statistics': statistics,
            'indexing_timestamp': datetime.now().isoformat(),
            'project_root': str(root_path)
        }

    def _generate_enhanced_statistics(self, indexed_files: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive statistics from indexed files."""
        stats = {
            'by_extension': {},
            'by_language': {},
            'by_directory': {},
            'complexity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0},
            'size_distribution': {'small': 0, 'medium': 0, 'large': 0, 'very_large': 0},
            'function_class_counts': {'total_functions': 0, 'total_classes': 0, 'total_imports': 0},
            'top_keywords': {},
            'chunk_size_distribution': {'small': 0, 'medium': 0, 'large': 0},
            'language_complexity': {}
        }

        for file_info in indexed_files:
            metadata = file_info['metadata']

            # Extension and language stats
            ext = metadata['file_extension']
            lang = metadata['language']
            stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
            stats['by_language'][lang] = stats['by_language'].get(lang, 0) + 1

            # Directory stats
            directory = metadata['directory']
            stats['by_directory'][directory] = stats['by_directory'].get(directory, 0) + 1

            # Complexity distribution
            complexity = metadata['complexity_score']
            if complexity < 5:
                stats['complexity_distribution']['low'] += 1
            elif complexity < 20:
                stats['complexity_distribution']['medium'] += 1
            elif complexity < 50:
                stats['complexity_distribution']['high'] += 1
            else:
                stats['complexity_distribution']['very_high'] += 1

            # Size distribution
            size_bytes = metadata['size_bytes']
            if size_bytes < 1024:  # < 1KB
                stats['size_distribution']['small'] += 1
            elif size_bytes < 10240:  # < 10KB
                stats['size_distribution']['medium'] += 1
            elif size_bytes < 102400:  # < 100KB
                stats['size_distribution']['large'] += 1
            else:
                stats['size_distribution']['very_large'] += 1

            # Function, class, import counts
            stats['function_class_counts']['total_functions'] += len(metadata['functions'])
            stats['function_class_counts']['total_classes'] += len(metadata['classes'])
            stats['function_class_counts']['total_imports'] += len(metadata['imports'])

            # Keyword frequency
            for keyword in metadata['keywords']:
                stats['top_keywords'][keyword] = stats['top_keywords'].get(keyword, 0) + 1

            # Language complexity tracking
            if lang not in stats['language_complexity']:
                stats['language_complexity'][lang] = {'total_complexity': 0, 'file_count': 0}
            stats['language_complexity'][lang]['total_complexity'] += complexity
            stats['language_complexity'][lang]['file_count'] += 1

            # Chunk size distribution
            for chunk_detail in file_info['chunk_details']:
                chunk_size = chunk_detail['content_length']
                if chunk_size < 500:
                    stats['chunk_size_distribution']['small'] += 1
                elif chunk_size < 1500:
                    stats['chunk_size_distribution']['medium'] += 1
                else:
                    stats['chunk_size_distribution']['large'] += 1

        # Sort top-level stats
        stats['by_extension'] = dict(sorted(stats['by_extension'].items(), key=lambda x: x[1], reverse=True))
        stats['by_language'] = dict(sorted(stats['by_language'].items(), key=lambda x: x[1], reverse=True))
        stats['by_directory'] = dict(sorted(stats['by_directory'].items(), key=lambda x: x[1], reverse=True)[:20])
        stats['top_keywords'] = dict(sorted(stats['top_keywords'].items(), key=lambda x: x[1], reverse=True)[:20])

        # Calculate average complexity by language
        for lang, data in stats['language_complexity'].items():
            data['average_complexity'] = data['total_complexity'] / data['file_count']

        return stats

    def save_index_report(self, index_data: Dict[str, Any], output_file: str = 'enhanced_index_report.json'):
        """Save comprehensive indexing report to file."""
        with open(output_file, 'w') as f:
            json.dump(index_data, f, indent=2, default=str)
        logger.info(f"Enhanced index report saved to: {output_file}")

    def create_collection_with_schema(self, collection_name: str, schema_config: Optional[Dict] = None) -> bool:
        """Create a collection with comprehensive schema configuration."""
        if schema_config is None:
            # Default configuration optimized for code search
            schema_config = self.create_collection_schema(
                collection_name=collection_name,
                vector_size=384,  # sentence-transformers/all-MiniLM-L6-v2
                distance_metric=DistanceMetric.COSINE,
                enable_quantization=True,
                quantization_type=QuantizationType.SCALAR,
                enable_sparse_vectors=True,
                replication_factor=1
            )

        return self.create_collection(collection_name, schema_config)


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced Codebase Indexer with Advanced Qdrant Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create collection with default schema
  %(prog)s create-collection my-codebase --qdrant-url http://localhost:6333 --api-key YOUR_KEY

  # Index directory with custom settings
  %(prog)s index /path/to/code --collection my-codebase --max-files 500

  # Create optimized collection for large codebase
  %(prog)s create-collection large-project --vector-size 768 --enable-quantization --replication-factor 2

  # List all collections
  %(prog)s list-collections

  # Get collection information
  %(prog)s collection-info my-codebase

  # Full workflow: create collection and index
  %(prog)s full-index /path/to/code --collection my-codebase --recreate
        """
    )

    # Connection settings
    parser.add_argument('--qdrant-url', required=True, help='Qdrant server URL')
    parser.add_argument('--api-key', required=True, help='Qdrant API key')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create collection command
    create_parser = subparsers.add_parser('create-collection', help='Create a new collection')
    create_parser.add_argument('collection_name', help='Name of the collection to create')
    create_parser.add_argument('--vector-size', type=int, default=384, help='Vector dimension size')
    create_parser.add_argument('--distance-metric', choices=['cosine', 'euclidean', 'dot', 'manhattan'],
                              default='cosine', help='Distance metric for vectors')
    create_parser.add_argument('--enable-quantization', action='store_true', help='Enable vector quantization')
    create_parser.add_argument('--quantization-type', choices=['scalar', 'product', 'binary'],
                              default='scalar', help='Type of quantization')
    create_parser.add_argument('--enable-sparse-vectors', action='store_true', help='Enable sparse vectors')
    create_parser.add_argument('--replication-factor', type=int, default=1, help='Replication factor')
    create_parser.add_argument('--shard-number', type=int, help='Number of shards (auto if not specified)')

    # Index directory command
    index_parser = subparsers.add_parser('index', help='Index a directory')
    index_parser.add_argument('path', help='Path to directory to index')
    index_parser.add_argument('--collection', required=True, help='Collection name to index into')
    index_parser.add_argument('--max-files', type=int, help='Maximum number of files to index')
    index_parser.add_argument('--max-chunk-size', type=int, default=1000, help='Maximum chunk size')
    index_parser.add_argument('--chunk-overlap', type=int, default=100, help='Chunk overlap size')
    index_parser.add_argument('--output-report', default='enhanced_index_report.json', help='Output report file')

    # Full index command (create collection + index)
    full_parser = subparsers.add_parser('full-index', help='Create collection and index directory')
    full_parser.add_argument('path', help='Path to directory to index')
    full_parser.add_argument('--collection', required=True, help='Collection name')
    full_parser.add_argument('--recreate', action='store_true', help='Delete and recreate collection')
    full_parser.add_argument('--max-files', type=int, help='Maximum number of files to index')
    full_parser.add_argument('--vector-size', type=int, default=384, help='Vector dimension size')
    full_parser.add_argument('--enable-quantization', action='store_true', help='Enable vector quantization')
    full_parser.add_argument('--enable-sparse-vectors', action='store_true', help='Enable sparse vectors')
    full_parser.add_argument('--output-report', default='enhanced_index_report.json', help='Output report file')

    # List collections command
    list_parser = subparsers.add_parser('list-collections', help='List all collections')

    # Collection info command
    info_parser = subparsers.add_parser('collection-info', help='Get collection information')
    info_parser.add_argument('collection_name', help='Name of the collection')

    # Delete collection command
    delete_parser = subparsers.add_parser('delete-collection', help='Delete a collection')
    delete_parser.add_argument('collection_name', help='Name of the collection to delete')
    delete_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize indexer
    indexer = EnhancedCodebaseIndexer(args.qdrant_url, args.api_key)

    try:
        if args.command == 'create-collection':
            # Map string values to enums
            distance_map = {
                'cosine': DistanceMetric.COSINE,
                'euclidean': DistanceMetric.EUCLIDEAN,
                'dot': DistanceMetric.DOT,
                'manhattan': DistanceMetric.MANHATTAN
            }
            quantization_map = {
                'scalar': QuantizationType.SCALAR,
                'product': QuantizationType.PRODUCT,
                'binary': QuantizationType.BINARY
            }

            schema_config = indexer.create_collection_schema(
                collection_name=args.collection_name,
                vector_size=args.vector_size,
                distance_metric=distance_map[args.distance_metric],
                enable_quantization=args.enable_quantization,
                quantization_type=quantization_map[args.quantization_type],
                enable_sparse_vectors=args.enable_sparse_vectors,
                replication_factor=args.replication_factor,
                shard_number=args.shard_number
            )

            success = indexer.create_collection(args.collection_name, schema_config)
            return 0 if success else 1

        elif args.command == 'index':
            root_path = Path(args.path)
            if not root_path.exists():
                logger.error(f"Path does not exist: {args.path}")
                return 1

            logger.info(f"Starting indexing of {root_path}")
            index_data = indexer.index_directory(root_path, args.max_files)

            # Print summary
            logger.info(f"\n=== Enhanced Indexing Summary ===")
            logger.info(f"Total files indexed: {index_data['total_files']}")
            logger.info(f"Total chunks created: {index_data['total_chunks']}")
            logger.info(f"Total points for insertion: {index_data['total_points']}")
            logger.info(f"Files skipped: {len(index_data['skipped_files'])}")

            stats = index_data['statistics']
            logger.info(f"\n=== Language Distribution ===")
            for lang, count in list(stats['by_language'].items())[:10]:
                logger.info(f"  {lang}: {count} files")

            logger.info(f"\n=== Complexity Analysis ===")
            for level, count in stats['complexity_distribution'].items():
                logger.info(f"  {level}: {count} files")

            # Save comprehensive report
            indexer.save_index_report(index_data, args.output_report)
            return 0

        elif args.command == 'full-index':
            root_path = Path(args.path)
            if not root_path.exists():
                logger.error(f"Path does not exist: {args.path}")
                return 1

            # Delete collection if recreate is requested
            if args.recreate:
                indexer.delete_collection(args.collection)

            # Create collection with advanced schema
            schema_config = indexer.create_collection_schema(
                collection_name=args.collection,
                vector_size=args.vector_size,
                enable_quantization=args.enable_quantization,
                enable_sparse_vectors=args.enable_sparse_vectors
            )

            if not indexer.create_collection(args.collection, schema_config):
                return 1

            # Index the directory
            logger.info(f"Starting full indexing workflow for {root_path}")
            index_data = indexer.index_directory(root_path, args.max_files)

            # Print comprehensive summary
            logger.info(f"\n=== Complete Indexing Results ===")
            logger.info(f"Collection: {args.collection}")
            logger.info(f"Total files indexed: {index_data['total_files']}")
            logger.info(f"Total chunks created: {index_data['total_chunks']}")
            logger.info(f"Files skipped: {len(index_data['skipped_files'])}")

            stats = index_data['statistics']
            logger.info(f"\nLanguages found: {len(stats['by_language'])}")
            logger.info(f"Functions extracted: {stats['function_class_counts']['total_functions']}")
            logger.info(f"Classes extracted: {stats['function_class_counts']['total_classes']}")
            logger.info(f"Import statements: {stats['function_class_counts']['total_imports']}")

            # Save report
            indexer.save_index_report(index_data, args.output_report)
            logger.info(f"\nCollection '{args.collection}' is ready for semantic search!")
            return 0

        elif args.command == 'list-collections':
            collections = indexer.list_collections()
            if collections:
                logger.info("\nExisting Collections:")
                for i, collection in enumerate(collections, 1):
                    name = collection.get('name', 'Unknown')
                    logger.info(f"  {i}. {name}")
            else:
                logger.info("No collections found.")
            return 0

        elif args.command == 'collection-info':
            info = indexer.get_collection_info(args.collection_name)
            if info:
                logger.info(f"\nCollection Information for '{args.collection_name}':")
                logger.info(json.dumps(info, indent=2))
            return 0

        elif args.command == 'delete-collection':
            if not args.confirm:
                response = input(f"Are you sure you want to delete collection '{args.collection_name}'? (y/N): ")
                if response.lower() != 'y':
                    logger.info("Operation cancelled.")
                    return 0

            success = indexer.delete_collection(args.collection_name)
            return 0 if success else 1

        else:
            parser.print_help()
            return 1

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
