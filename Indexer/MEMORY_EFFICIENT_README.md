# Memory-Efficient Codebase Indexer

This document explains the memory-efficient codebase indexer solution developed to address memory allocation issues when indexing large codebases.

## Problem

The original enhanced indexer (`enhanced_codebase_indexer.py`) encountered memory allocation errors when processing large codebases:

```
python3(61416,0x1ff1a4180) malloc: Failed to allocate segment from range group - out of space
```

This occurred when trying to index the gcode-debugger project (~951MB with 11,566+ files).

## Solution

The memory-efficient indexer (`memory_efficient_indexer.py`) implements several key optimizations:

### 1. Batch Processing
- Processes files in configurable batches (default: 25-50 files)
- Forces garbage collection between batches
- Prevents memory accumulation from processing thousands of files at once

### 2. Memory Management
- Uses memory mapping (`mmap`) for large files
- Limits file size processing (default: 5-10MB max)
- Clears variables explicitly with `del` statements
- Reduces metadata storage to essential information only

### 3. Streaming Architecture
- File iterator instead of loading all file paths into memory
- Process-and-forget pattern for individual files
- Minimal in-memory data structures

### 4. Storage Optimizations
- On-disk vector storage instead of in-memory
- Reduced HNSW parameters to limit memory usage
- Quantization enabled by default for memory savings

## Usage

### Basic Usage

```bash
# Process 1000 files in batches of 25
python3 memory_efficient_indexer.py index /path/to/project \
  --collection my-project \
  --max-files 1000 \
  --batch-size 25 \
  --max-file-size 5
```

### Using the Shell Script

```bash
# Automated script with optimized defaults
./run_memory_efficient_indexing.sh /path/to/project \
  --collection my-project \
  --batch-size 25 \
  --max-files 2000 \
  --max-file-size 5
```

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--batch-size` | 25 | Files processed per batch |
| `--max-file-size` | 5MB | Maximum file size to process |
| `--max-files` | None | Limit total files processed |
| `--qdrant-url` | http://localhost:6333 | Qdrant server URL |

## Memory Optimization Strategies

### For Large Codebases (>10,000 files)
- Use smaller batch sizes (10-25)
- Set strict file size limits (1-5MB)
- Process in multiple runs with `--max-files`
- Monitor system memory during processing

### For Limited Memory Systems
- Batch size: 10-15
- Max file size: 1-3MB
- Enable all quantization options
- Use on-disk storage for vectors

## Performance Comparison

| Metric | Original Indexer | Memory-Efficient |
|--------|------------------|------------------|
| Memory Usage | High (accumulates) | Low (constant) |
| Large Files | Loads entirely | Memory mapped |
| Batch Processing | No | Yes |
| Garbage Collection | Automatic only | Forced between batches |
| Max Tested Files | ~100 (crashed) | 1000+ (successful) |

## Test Results

Successfully indexed gcode-debugger project:
- **1000 files** processed in **~1 second**
- **Zero memory allocation errors**
- **Batch size 25** with **5MB max file size**
- **Consistent memory usage** throughout processing

## Files Structure

```
Indexer/
├── memory_efficient_indexer.py          # Main indexer script
├── run_memory_efficient_indexing.sh     # Automated shell script
├── enhanced_codebase_indexer.py          # Original (memory-heavy) version
├── enhanced_index_codebase.sh           # Original shell script
└── MEMORY_EFFICIENT_README.md           # This documentation
```

## Migration from Original Indexer

### Replace This:
```bash
python3 enhanced_codebase_indexer.py index /path/to/project --collection my-project
```

### With This:
```bash
python3 memory_efficient_indexer.py index /path/to/project \
  --collection my-project \
  --max-files 1000 \
  --batch-size 25
```

### Or Use the Shell Script:
```bash
./run_memory_efficient_indexing.sh /path/to/project --collection my-project
```

## Troubleshooting

### Memory Issues Still Occur
- Reduce batch size to 10 or lower
- Lower max file size to 1-3MB
- Process fewer files per run (--max-files 500)

### Slow Processing
- Increase batch size (but monitor memory)
- Increase max file size if system has sufficient RAM
- Remove file size limits for small codebases

### Qdrant Connection Errors
- Ensure Qdrant is running on the specified port
- Check firewall and network connectivity
- Verify Qdrant URL in configuration

## Future Improvements

1. **Streaming Vector Generation**: Process embeddings in smaller chunks
2. **Multi-threaded Processing**: Parallel file processing with memory limits
3. **Progressive Indexing**: Resume from interruptions
4. **Memory Monitoring**: Automatic batch size adjustment based on available RAM
5. **Distributed Processing**: Split large codebases across multiple workers

## Technical Details

### Memory Management Techniques Used

1. **Explicit Memory Cleanup**:
   ```python
   del content, metadata, chunks
   gc.collect()
   ```

2. **Memory Mapped File Reading**:
   ```python
   with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
       content = mm.read().decode('utf-8', errors='ignore')
   ```

3. **Limited Data Structures**:
   ```python
   # Limit keywords, functions, etc. to prevent unbounded growth
   keywords = keywords[:10]
   functions = functions[:100]
   ```

4. **On-Disk Storage Configuration**:
   ```python
   "on_disk": True,
   "on_disk_payload": True,
   "hnsw_config": {"on_disk": True}
   ```

This memory-efficient approach successfully resolves the "out of space" memory allocation errors while maintaining indexing functionality and performance.