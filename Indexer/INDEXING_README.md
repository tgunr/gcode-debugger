# Codebase Indexing System

A comprehensive tool for indexing codebases and creating searchable collections in Qdrant vector database. This system enables semantic search across your codebase, making it easier to find relevant code, understand relationships, and explore large projects.

## Overview

This indexing system provides:
- **Automated codebase scanning** with intelligent file filtering
- **Qdrant collection management** (create, delete, update)
- **Semantic chunking** for optimal embedding generation
- **Comprehensive metadata extraction** including complexity analysis
- **Detailed reporting** with statistics and insights
- **Multiple indexing strategies** for different project types

## Quick Start

### Prerequisites

1. **Python 3.7+** with pip
2. **Qdrant server** running and accessible
3. **Required Python packages**:
   ```bash
   pip install -r indexing_requirements.txt
   ```

### Basic Usage

1. **Configure your Qdrant connection** in `indexing_config.json`:
   ```json
   {
     "qdrant": {
       "url": "https://your-qdrant-server:6333",
       "api_key": "your-api-key"
     }
   }
   ```

2. **Index a codebase**:
   ```bash
   # Index bbctrl-firmware
   ./index_codebase.sh index-bbctrl

   # Index gcode-debugger
   ./index_codebase.sh index-debugger

   # Index custom directory
   ./index_codebase.sh index-custom /path/to/your/project
   ```

3. **Manage collections**:
   ```bash
   # List all collections
   ./index_codebase.sh list-collections

   # Get collection info
   ./index_codebase.sh info my-collection

   # Delete a collection
   ./index_codebase.sh delete old-collection
   ```

## Detailed Usage

### Command Line Interface

The main script `index_codebase.sh` provides a convenient interface:

```bash
# Basic indexing commands
./index_codebase.sh index-bbctrl           # Index bbctrl-firmware
./index_codebase.sh index-debugger         # Index gcode-debugger
./index_codebase.sh index-custom PATH      # Index custom directory

# Collection management
./index_codebase.sh list-collections       # List existing collections
./index_codebase.sh info COLLECTION        # Get collection information
./index_codebase.sh delete COLLECTION      # Delete a collection

# Advanced options
./index_codebase.sh -n "custom-name" index-bbctrl    # Custom collection name
./index_codebase.sh -m 100 index-debugger            # Limit to 100 files
./index_codebase.sh -r index-bbctrl                  # Recreate collection
./index_codebase.sh -R index-debugger                # Report only (no indexing)
```

### Python API

For programmatic access, use the `CodebaseIndexer` class directly:

```python
from codebase_indexer import CodebaseIndexer
from pathlib import Path

# Initialize indexer
indexer = CodebaseIndexer(
    qdrant_url="https://your-qdrant:6333",
    api_key="your-api-key",
    collection_name="my-project"
)

# Create collection
indexer.create_collection(vector_size=384)

# Index directory
root_path = Path("/path/to/your/project")
index_data = indexer.index_directory(root_path, max_files=500)

# Save report
indexer.save_index_report(index_data, "my-project-report.json")
```

## Configuration

The `indexing_config.json` file controls all aspects of the indexing process:

### Qdrant Settings
```json
{
  "qdrant": {
    "url": "http://localhost:6333",
    "api_key": "your-jwt-token",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "vector_size": 384
  }
}
```

### File Filtering
```json
{
  "indexing": {
    "supported_extensions": [
      ".py", ".js", ".ts", ".cpp", ".java", ".md", ".json"
    ],
    "exclude_patterns": [
      ".git", "__pycache__", "node_modules", "build", "dist"
    ],
    "include_dotfiles": [
      ".gitignore", ".dockerignore", ".env.example"
    ]
  }
}
```

### Project Collections
```json
{
  "collections": {
    "bbctrl-firmware": {
      "name": "bbctrl-firmware-codebase",
      "path": "/Volumes/Work/Buildbotics/bbctrl-firmware",
      "focus_areas": ["firmware", "cnc", "control"]
    }
  }
}
```

## Features

### Intelligent File Processing

- **Smart filtering** excludes build artifacts, dependencies, and temporary files
- **Extension-based** inclusion with comprehensive language support
- **Size limits** prevent processing of extremely large files
- **Encoding detection** handles various text encodings gracefully

### Metadata Extraction

Each indexed file includes rich metadata:
- **Basic info**: path, size, modification time, file hash
- **Content metrics**: line counts, complexity scores
- **Code analysis**: keyword density, structural patterns
- **Project context**: relative paths, directory hierarchies

### Semantic Chunking

- **Intelligent splitting** preserves code structure and context
- **Configurable chunk sizes** balance detail with performance
- **Overlap handling** prevents information loss at boundaries
- **Language-aware** chunking for different file types

### Comprehensive Reporting

Generated reports include:
- **File statistics** by extension, directory, and complexity
- **Processing summary** with success/failure counts
- **Content previews** for quick review
- **Error logs** for troubleshooting

## Supported File Types

The indexer supports a wide range of file types:

### Programming Languages
- **Python**: `.py`
- **JavaScript/TypeScript**: `.js`, `.ts`, `.jsx`, `.tsx`
- **C/C++**: `.c`, `.cpp`, `.h`, `.hpp`
- **Java**: `.java`
- **C#**: `.cs`
- **Go**: `.go`
- **Rust**: `.rs`
- **PHP**: `.php`
- **Ruby**: `.rb`

### Web Technologies
- **HTML**: `.html`, `.htm`
- **CSS**: `.css`, `.scss`, `.less`
- **XML**: `.xml`

### Configuration & Data
- **JSON**: `.json`
- **YAML**: `.yaml`, `.yml`
- **TOML**: `.toml`
- **INI**: `.ini`, `.cfg`, `.conf`
- **SQL**: `.sql`

### Documentation
- **Markdown**: `.md`
- **reStructuredText**: `.rst`
- **Plain text**: `.txt`

### Scripts & Build Files
- **Shell**: `.sh`
- **Batch**: `.bat`
- **PowerShell**: `.ps1`
- **Docker**: `.dockerfile`
- **Make**: `.makefile`

## Example Workflows

### 1. Initial Project Setup

```bash
# Create a new collection for your project
./index_codebase.sh -n "my-project-v1" index-custom /path/to/project

# Verify the collection was created
./index_codebase.sh info my-project-v1

# Generate a comprehensive report
./index_codebase.sh -R -o project-analysis.json index-custom /path/to/project
```

### 2. Incremental Updates

```bash
# Update existing collection with new/changed files
./index_codebase.sh -r index-bbctrl

# Compare before and after by examining reports
diff old-report.json new-report.json
```

### 3. Multi-Project Analysis

```bash
# Index multiple related projects
./index_codebase.sh -n "frontend-code" index-custom /path/to/frontend
./index_codebase.sh -n "backend-code" index-custom /path/to/backend
./index_codebase.sh -n "shared-libs" index-custom /path/to/libraries

# List all project collections
./index_codebase.sh list-collections
```

### 4. Development Workflow Integration

```bash
# Before major refactoring - create snapshot
./index_codebase.sh -n "pre-refactor-$(date +%Y%m%d)" index-custom .

# During development - quick updates with limits
./index_codebase.sh -m 50 index-custom .

# Post-development - full reindex
./index_codebase.sh -r index-custom .
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Verify Qdrant server is running and accessible
   - Check API key format and permissions
   - Confirm network connectivity

2. **Large File Processing**
   - Use `--max-files` to limit batch size
   - Check disk space for temporary files
   - Monitor memory usage during processing

3. **Permission Errors**
   - Ensure read permissions on source directories
   - Check write permissions for report output
   - Verify Qdrant collection permissions

### Debug Mode

Enable verbose output for troubleshooting:
```bash
./index_codebase.sh -v index-custom /path/to/project
```

### Log Analysis

Check the generated reports for detailed processing information:
```bash
# View processing summary
jq '.statistics' index_report.json

# Check for skipped files
jq '.skipped_files' index_report.json

# Analyze file distribution
jq '.statistics.by_extension' index_report.json
```

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Use `--max-files` for large codebases
2. **Selective Indexing**: Customize `exclude_patterns` to skip irrelevant files
3. **Chunk Sizing**: Adjust `max_chunk_size` based on your use case
4. **Collection Management**: Regularly clean up unused collections

### Resource Usage

- **Memory**: ~50-100MB per 1000 files (depends on file sizes)
- **Storage**: Varies by collection size and vector dimensions
- **Network**: Bandwidth usage depends on chunk sizes and batch frequency

## Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions example
- name: Index Codebase
  run: |
    ./index_codebase.sh -n "build-${{ github.run_number }}" index-custom .

- name: Upload Report
  uses: actions/upload-artifact@v2
  with:
    name: indexing-report
    path: index_report.json
```

### Development Scripts

```bash
#!/bin/bash
# pre-commit hook
./index_codebase.sh -R -o pre-commit-report.json index-custom .
echo "Codebase indexed. Check pre-commit-report.json for details."
```

## API Reference

### CodebaseIndexer Class

#### Constructor
```python
CodebaseIndexer(qdrant_url: str, api_key: str, collection_name: str)
```

#### Methods

##### Collection Management
- `create_collection(vector_size: int = 384) -> bool`
- `delete_collection() -> bool`
- `get_collection_info() -> Optional[Dict]`

##### Indexing Operations
- `index_directory(root_path: Path, max_files: Optional[int] = None) -> Dict[str, Any]`
- `save_index_report(index_data: Dict[str, Any], output_file: str)`

##### Content Processing
- `get_file_content(file_path: Path) -> Optional[str]`
- `extract_file_metadata(file_path: Path, content: str) -> Dict[str, Any]`
- `chunk_content(content: str, max_chunk_size: int = 1000) -> List[str]`

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Add tests** for new functionality
4. **Update documentation** as needed
5. **Submit a pull request**

### Development Setup

```bash
# Clone repository
git clone <repository-url>

# Install dependencies
pip install -r indexing_requirements.txt

# Run tests
pytest tests/

# Format code
black codebase_indexer.py

# Lint code
flake8 codebase_indexer.py
```

## License

This project is licensed under the same terms as the parent project. See LICENSE file for details.

## Support

For questions and support:
1. Check the troubleshooting section above
2. Review the configuration examples
3. Examine the generated report files for insights
4. Create an issue with detailed error information

## Changelog

### Version 1.0.0
- Initial release with core indexing functionality
- Qdrant collection management
- Comprehensive file type support
- Metadata extraction and analysis
- Command-line interface
- Configuration system

---

*This indexing system is designed to grow with your codebase and adapt to your specific needs. Customize the configuration and extend the functionality as your project evolves.*
