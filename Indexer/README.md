# Codebase Indexer

A comprehensive system for indexing codebases and creating searchable collections in Qdrant vector databases. This directory contains both basic and enhanced indexing tools with advanced semantic search capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- Qdrant server (local or cloud)
- Required Python packages: `pip install -r indexing_requirements.txt`

### Basic Usage

```bash
# Enhanced indexer (recommended)
./enhanced_index_codebase.sh health-check
./enhanced_index_codebase.sh index-bbctrl
./enhanced_index_codebase.sh index-debugger

# Basic indexer
./index_codebase.sh index-bbctrl
./index_codebase.sh index-debugger
```

## 📁 Files Overview

### Core Indexers
- **`enhanced_codebase_indexer.py`** - Advanced indexer with production-grade features
- **`codebase_indexer.py`** - Basic indexer for simple use cases

### Convenience Scripts
- **`enhanced_index_codebase.sh`** - Feature-rich shell interface (recommended)
- **`index_codebase.sh`** - Basic shell interface

### Configuration
- **`enhanced_indexing_config.json`** - Comprehensive configuration with templates
- **`indexing_config.json`** - Basic configuration

### Documentation
- **`ENHANCED_INDEXING_README.md`** - Detailed guide for the enhanced system
- **`INDEXING_README.md`** - Basic indexer documentation

### Utilities
- **`demo_enhanced_indexing.py`** - Interactive demonstration script
- **`indexing_requirements.txt`** - Python dependencies

## 🔧 Configuration

Edit the configuration files with your Qdrant connection details:

```json
{
  "qdrant": {
    "url": "https://your-qdrant-server:6333",
    "api_key": "your-jwt-token-here"
  }
}
```

## 🌟 Features

### Enhanced Indexer (Recommended)
- **🧠 Intelligent Code Analysis**: 30+ programming languages with structure extraction
- **⚡ High-Performance**: Parallel processing, memory optimization, caching
- **🏗️ Production-Ready**: Quantization, sharding, replication, health monitoring
- **📊 Deep Analytics**: Complexity analysis, comprehensive reporting
- **🔍 Hybrid Search**: Dense + sparse vectors for semantic and keyword search

### Basic Indexer
- **Simple Setup**: Quick start for small projects
- **Core Features**: File filtering, chunking, metadata extraction
- **Basic Analytics**: File statistics and processing reports

## 📖 Usage Examples

### Enhanced System

```bash
# Create optimized collection
./enhanced_index_codebase.sh create-collection my-code medium_codebase

# Full indexing with smart features
./enhanced_index_codebase.sh \
  --smart-chunking \
  --parallel \
  --enable-quantization \
  full-index /path/to/code my-code

# Advanced analysis
./enhanced_index_codebase.sh analyze-codebase /path/to/code

# Maintenance operations
./enhanced_index_codebase.sh health-check
./enhanced_index_codebase.sh compare-collections v1 v2
./enhanced_index_codebase.sh backup-collection important-data
```

### Basic System

```bash
# Index with basic settings
./index_codebase.sh index-custom /path/to/code

# Generate report only
./index_codebase.sh -R index-custom /path/to/code

# List collections
./index_codebase.sh list-collections
```

## 🎯 Collection Templates (Enhanced)

| Template | Use Case | Features |
|----------|----------|-----------|
| **small_codebase** | < 10K files | Fast indexing, single shard, no quantization |
| **medium_codebase** | 10K-100K files | Balanced performance, scalar quantization |
| **large_codebase** | 100K+ files | Memory optimized, product quantization |
| **high_performance** | Production | Maximum reliability, high availability |

## 🔍 Language Support

**Tier 1 (Advanced Analysis)**:
Python, JavaScript, TypeScript, Java, C/C++, Go, Rust

**Tier 2 (Structure Analysis)**:
C#, PHP, Ruby, Swift, Kotlin, Scala

**Tier 3 (Basic Support)**:
Shell, PowerShell, SQL, HTML/CSS, XML/JSON, Markdown, and more

## 📊 Analytics & Reporting

The system generates comprehensive reports including:
- Language distribution and complexity analysis
- Code quality metrics and technical debt indicators
- Performance insights and storage efficiency
- Search performance benchmarks

## 🚨 Getting Help

1. **Enhanced System**: See `ENHANCED_INDEXING_README.md` for detailed documentation
2. **Basic System**: See `INDEXING_README.md` for basic usage
3. **Interactive Demo**: Run `python3 demo_enhanced_indexing.py`
4. **Command Help**: Use `--help` flag with any script

## 🔧 Troubleshooting

### Connection Issues
```bash
# Test connectivity
./enhanced_index_codebase.sh health-check
```

### Performance Issues
```bash
# Reduce memory usage
./enhanced_index_codebase.sh --memory-limit 1024 index-custom /path
```

### Debug Mode
```bash
# Enable verbose logging
./enhanced_index_codebase.sh --verbose command
```

## 🔄 Migration

### From Basic to Enhanced
1. Backup existing collections
2. Export configuration settings
3. Use enhanced indexer with similar templates
4. Validate search performance

### Schema Updates
The enhanced system supports schema migration and collection optimization for existing setups.

## 🤝 Contributing

1. Follow Python PEP 8 style guidelines
2. Add tests for new features
3. Update documentation
4. Profile performance changes

## 📚 Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Vector Search Best Practices](https://qdrant.tech/articles/)
- [Sentence Transformers](https://www.sbert.net/)

---

**Recommendation**: Start with the enhanced indexer for new projects. It provides enterprise-grade features with production-ready performance and comprehensive analytics.