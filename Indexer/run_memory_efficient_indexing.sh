#!/bin/bash

# Memory-Efficient Codebase Indexing Script
# This script runs the memory-efficient indexer with optimized settings

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INDEXER_SCRIPT="${SCRIPT_DIR}/memory_efficient_indexer.py"
DEFAULT_QDRANT_URL="http://localhost:6333"
DEFAULT_BATCH_SIZE=25
DEFAULT_MAX_FILE_SIZE=5
DEFAULT_MAX_FILES=1000

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi

    if [ ! -f "$INDEXER_SCRIPT" ]; then
        print_error "Indexer script not found: $INDEXER_SCRIPT"
        exit 1
    fi
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] <directory> --collection <collection_name>

Memory-Efficient Codebase Indexing with optimized settings

Options:
    --collection <name>     Collection name (required)
    --qdrant-url <url>      Qdrant URL (default: $DEFAULT_QDRANT_URL)
    --batch-size <size>     Batch size for processing (default: $DEFAULT_BATCH_SIZE)
    --max-file-size <mb>    Maximum file size in MB (default: $DEFAULT_MAX_FILE_SIZE)
    --max-files <count>     Maximum number of files to index (default: $DEFAULT_MAX_FILES)
    --output-report <file>  Output report file (default: memory_efficient_index_report.json)
    --create-collection     Create collection before indexing
    --skip-qdrant-check     Skip Qdrant connection check (offline analysis only)
    --help                  Show this help message

Examples:
    $0 /path/to/project --collection my-project
    $0 /path/to/project --collection my-project --batch-size 10 --max-files 500
    $0 /path/to/project --collection my-project --create-collection

Memory Optimization Tips:
    - Use smaller batch sizes (10-25) for large codebases
    - Set max-file-size to 1-5MB to skip very large files
    - Use max-files to limit initial indexing runs
    - Monitor system memory usage during indexing

EOF
}

check_qdrant_connection() {
    local url="$1"
    local skip_check="$2"

    if [[ "$skip_check" == "true" ]]; then
        print_warning "Skipping Qdrant connection check (offline mode)"
        return 0
    fi

    print_info "Checking Qdrant connection at $url..."

    if ! curl -s -f "$url/health" > /dev/null; then
        print_error "Cannot connect to Qdrant at $url"
        print_error "Please make sure Qdrant is running or use --skip-qdrant-check for offline analysis"
        exit 1
    fi

    print_success "Qdrant connection OK"
}

# Parse command line arguments
DIRECTORY=""
COLLECTION=""
QDRANT_URL="$DEFAULT_QDRANT_URL"
BATCH_SIZE="$DEFAULT_BATCH_SIZE"
MAX_FILE_SIZE="$DEFAULT_MAX_FILE_SIZE"
MAX_FILES="$DEFAULT_MAX_FILES"
OUTPUT_REPORT=""
CREATE_COLLECTION=false
SKIP_QDRANT_CHECK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --collection)
            COLLECTION="$2"
            shift 2
            ;;
        --qdrant-url)
            QDRANT_URL="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --max-file-size)
            MAX_FILE_SIZE="$2"
            shift 2
            ;;
        --max-files)
            MAX_FILES="$2"
            shift 2
            ;;
        --output-report)
            OUTPUT_REPORT="$2"
            shift 2
            ;;
        --create-collection)
            CREATE_COLLECTION=true
            shift
            ;;
        --skip-qdrant-check)
            SKIP_QDRANT_CHECK=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [ -z "$DIRECTORY" ]; then
                DIRECTORY="$1"
            else
                print_error "Multiple directories specified"
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [ -z "$DIRECTORY" ]; then
    print_error "Directory argument is required"
    show_usage
    exit 1
fi

if [ -z "$COLLECTION" ]; then
    print_error "--collection argument is required"
    show_usage
    exit 1
fi

if [ ! -d "$DIRECTORY" ]; then
    print_error "Directory does not exist: $DIRECTORY"
    exit 1
fi

# Set default output report if not specified
if [ -z "$OUTPUT_REPORT" ]; then
    OUTPUT_REPORT="${COLLECTION}_memory_efficient_report.json"
fi

# Check requirements
check_requirements

# Check Qdrant connection
check_qdrant_connection "$QDRANT_URL" "$SKIP_QDRANT_CHECK"

# Print configuration
print_info "=== Memory-Efficient Indexing Configuration ==="
print_info "Directory: $DIRECTORY"
print_info "Collection: $COLLECTION"
print_info "Qdrant URL: $QDRANT_URL"
print_info "Batch Size: $BATCH_SIZE"
print_info "Max File Size: ${MAX_FILE_SIZE}MB"
print_info "Max Files: $MAX_FILES"
print_info "Output Report: $OUTPUT_REPORT"
print_info "Create Collection: $CREATE_COLLECTION"
print_info "Skip Qdrant Check: $SKIP_QDRANT_CHECK"

# Get directory size and file count for estimation
DIR_SIZE=$(du -sh "$DIRECTORY" 2>/dev/null | cut -f1 || echo "unknown")
FILE_COUNT=$(find "$DIRECTORY" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.json" -o -name "*.md" \) | wc -l)

print_info "Project size: $DIR_SIZE"
print_info "Estimated indexable files: $FILE_COUNT"

if [ "$FILE_COUNT" -gt 10000 ]; then
    print_warning "Large number of files detected ($FILE_COUNT)"
    print_warning "Consider using --max-files to limit initial indexing"
fi

# Create collection if requested
if [ "$CREATE_COLLECTION" = true ] && [ "$SKIP_QDRANT_CHECK" = false ]; then
    print_info "Creating collection: $COLLECTION"
    if python3 "$INDEXER_SCRIPT" create-collection "$COLLECTION" --qdrant-url "$QDRANT_URL"; then
        print_success "Collection created successfully"
    else
        print_error "Failed to create collection"
        exit 1
    fi
elif [ "$CREATE_COLLECTION" = true ] && [ "$SKIP_QDRANT_CHECK" = true ]; then
    print_warning "Skipping collection creation in offline mode"
fi

# Start indexing
print_info "Starting memory-efficient indexing..."
print_info "This may take a while for large codebases..."

start_time=$(date +%s)

if python3 "$INDEXER_SCRIPT" index "$DIRECTORY" \
    --collection "$COLLECTION" \
    --qdrant-url "$QDRANT_URL" \
    --batch-size "$BATCH_SIZE" \
    --max-file-size "$MAX_FILE_SIZE" \
    --max-files "$MAX_FILES" \
    --output-report "$OUTPUT_REPORT"; then

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    print_success "Indexing completed successfully!"
    print_success "Duration: ${duration} seconds"
    print_success "Report saved to: $OUTPUT_REPORT"

    # Show quick stats from report if it exists
    if [ -f "$OUTPUT_REPORT" ] && command -v jq &> /dev/null; then
        print_info "=== Quick Statistics ==="
        TOTAL_FILES=$(jq -r '.total_files' "$OUTPUT_REPORT" 2>/dev/null || echo "unknown")
        SKIPPED_FILES=$(jq -r '.skipped_files | length' "$OUTPUT_REPORT" 2>/dev/null || echo "unknown")
        print_info "Files indexed: $TOTAL_FILES"
        print_info "Files skipped: $SKIPPED_FILES"
    fi
else
    print_error "Indexing failed"
    exit 1
fi

print_success "Memory-efficient indexing complete!"
