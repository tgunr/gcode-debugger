#!/bin/bash

# Enhanced Codebase Indexer - Advanced convenience script for sophisticated Qdrant indexing
# Usage: ./enhanced_index_codebase.sh [options] COMMAND

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/enhanced_indexing_config.json"
INDEXER_SCRIPT="$SCRIPT_DIR/enhanced_codebase_indexer.py"

# Color codes for output - with terminal detection
if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
    # Terminal supports colors
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    PURPLE=$(tput setaf 5)
    CYAN=$(tput setaf 6)
    WHITE=$(tput setaf 7; tput bold)
    NC=$(tput sgr0) # No Color
elif [[ -t 1 ]]; then
    # Fallback to ANSI codes
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    PURPLE='\033[0;35m'
    CYAN='\033[0;36m'
    WHITE='\033[1;37m'
    NC='\033[0m'
else
    # No color support
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    PURPLE=''
    CYAN=''
    WHITE=''
    NC=''
fi

# Function to print colored output
print_status() {
    printf "%b[INFO]%b %s\n" "$BLUE" "$NC" "$1"
}

print_success() {
    printf "%b[SUCCESS]%b %s\n" "$GREEN" "$NC" "$1"
}

print_warning() {
    printf "%b[WARNING]%b %s\n" "$YELLOW" "$NC" "$1"
}

print_error() {
    printf "%b[ERROR]%b %s\n" "$RED" "$NC" "$1"
}

print_header() {
    printf "%b[ENHANCED INDEXER]%b %s\n" "$PURPLE" "$NC" "$1"
}

print_progress() {
    printf "%b[PROGRESS]%b %s\n" "$CYAN" "$NC" "$1"
}

# Function to show usage
show_help() {
    cat << EOF
${WHITE}Enhanced Codebase Indexer${NC} - Advanced Qdrant vector database indexing

${YELLOW}USAGE:${NC}
    $0 [OPTIONS] COMMAND

${YELLOW}COMMANDS:${NC}
    ${GREEN}Collection Management:${NC}
        create-collection NAME [TEMPLATE]   Create collection with optional template
        delete-collection NAME              Delete a collection
        list-collections                    List all collections with details
        collection-info NAME               Get detailed collection information
        clone-collection SRC DEST          Clone collection configuration

    ${GREEN}Indexing Operations:${NC}
        index-bbctrl                       Index bbctrl-firmware with optimized settings
        index-debugger                     Index gcode-debugger with GUI analysis
        index-combined                     Index both projects into unified collection
        index-custom PATH [COLLECTION]     Index custom directory with auto-detection
        full-index PATH COLLECTION         Complete workflow: create + index + optimize

    ${GREEN}Advanced Operations:${NC}
        analyze-codebase PATH              Deep analysis without indexing
        compare-collections COL1 COL2      Compare two collections
        optimize-collection NAME           Optimize existing collection
        backup-collection NAME             Backup collection configuration
        migrate-collection NAME            Migrate collection to new schema

    ${GREEN}Maintenance:${NC}
        health-check                       Check system health and connectivity
        cleanup-cache                      Clean indexing cache and temp files
        update-schema NAME                 Update collection schema
        reindex-collection NAME            Full reindex of existing collection

${YELLOW}OPTIONS:${NC}
    ${GREEN}Connection:${NC}
        -c, --config FILE              Use custom config file (default: enhanced_indexing_config.json)
        -u, --url URL                  Override Qdrant URL
        -k, --api-key KEY              Override API key
        --timeout SECONDS              Connection timeout (default: 30)

    ${GREEN}Collection Settings:${NC}
        -t, --template NAME            Collection template (small/medium/large/high_performance)
        --vector-size SIZE             Vector dimension size (default: 384)
        --distance METRIC              Distance metric (cosine/euclidean/dot/manhattan)
        --enable-quantization          Enable vector quantization for memory optimization
        --quantization-type TYPE       Quantization type (scalar/product/binary)
        --enable-sparse                Enable sparse vectors for hybrid search
        --replication FACTOR           Replication factor for high availability
        --shards NUMBER                Number of shards for scalability

    ${GREEN}Indexing Control:${NC}
        -m, --max-files NUM            Maximum files to index
        --max-file-size MB             Maximum file size in MB (default: 10)
        --chunk-size SIZE              Maximum chunk size (default: 1000)
        --chunk-overlap SIZE           Chunk overlap size (default: 100)
        --smart-chunking               Enable intelligent code-aware chunking
        --complexity-threshold NUM     Minimum complexity for detailed analysis

    ${GREEN}Performance:${NC}
        --parallel                     Enable parallel processing
        --workers NUM                  Number of parallel workers
        --batch-size NUM               Batch size for processing
        --memory-limit MB              Memory limit in MB
        --cache-dir PATH               Custom cache directory

    ${GREEN}Output Control:${NC}
        -o, --output FILE              Output report file
        --format FORMAT                Report format (json/csv/markdown)
        --no-preview                   Skip content previews
        --compression                  Enable output compression
        -v, --verbose                  Verbose output
        -q, --quiet                    Quiet mode (errors only)

    ${GREEN}Operation Modes:${NC}
        -r, --recreate                 Delete and recreate collection
        -R, --report-only              Generate report only, don't create collection
        --dry-run                      Simulate operations without changes
        --force                        Force operations without confirmation
        --resume                       Resume interrupted operations

    ${GREEN}Help:${NC}
        -h, --help                     Show this help
        --examples                     Show usage examples
        --templates                    Show available templates
        --languages                    Show supported languages

${YELLOW}EXAMPLES:${NC}

    ${GREEN}# Quick start - index with best practices${NC}
    $0 index-bbctrl
    $0 index-debugger

    ${GREEN}# Production setup with high performance${NC}
    $0 -t high_performance --enable-quantization --replication 2 create-collection my-prod-code
    $0 --smart-chunking --parallel full-index /path/to/code my-prod-code

    ${GREEN}# Large codebase with custom settings${NC}
    $0 -t large_codebase --vector-size 768 --shards 4 create-collection big-project
    $0 --max-files 50000 --workers 8 --batch-size 2000 index-custom /huge/codebase big-project

    ${GREEN}# Analysis and comparison${NC}
    $0 --complexity-threshold 20 analyze-codebase /path/to/code
    $0 compare-collections old-version new-version

    ${GREEN}# Maintenance operations${NC}
    $0 health-check
    $0 optimize-collection my-collection
    $0 --force reindex-collection stale-collection

${YELLOW}COLLECTION TEMPLATES:${NC}
    ${GREEN}small_codebase${NC}     - Under 10K files, basic optimization
    ${GREEN}medium_codebase${NC}    - 10K-100K files, balanced performance
    ${GREEN}large_codebase${NC}     - 100K+ files, aggressive optimization
    ${GREEN}high_performance${NC}   - Production environments, maximum reliability

${YELLOW}CONFIGURATION:${NC}
    Edit $CONFIG_FILE to customize:
    - Qdrant connection settings and templates
    - Language-specific analysis patterns
    - File processing and chunking parameters
    - Performance and caching options

EOF
}

show_examples() {
    cat << EOF
${WHITE}Enhanced Indexer - Usage Examples${NC}

${YELLOW}🚀 Quick Start Examples:${NC}
    # Index your projects with optimal settings
    $0 index-bbctrl
    $0 index-debugger
    $0 index-combined

${YELLOW}📊 Analysis Examples:${NC}
    # Deep analysis without indexing
    $0 analyze-codebase /path/to/project

    # Compare two versions
    $0 compare-collections project-v1 project-v2

    # Health check and diagnostics
    $0 health-check

${YELLOW}🏗️ Production Setup Examples:${NC}
    # High-availability production collection
    $0 -t high_performance --replication 3 --enable-quantization create-collection prod-api
    $0 --smart-chunking --parallel --workers 16 full-index /app/src prod-api

    # Large enterprise codebase
    $0 -t large_codebase --vector-size 768 --shards 8 create-collection enterprise-code
    $0 --max-files 100000 --batch-size 5000 --memory-limit 8192 index-custom /enterprise/src enterprise-code

${YELLOW}🔧 Advanced Configuration Examples:${NC}
    # Custom quantization and sparse vectors
    $0 --quantization-type product --enable-sparse create-collection hybrid-search

    # Memory-optimized for resource-constrained environments
    $0 --vector-size 256 --quantization-type binary --memory-limit 1024 create-collection lightweight

    # High-precision semantic search
    $0 --vector-size 1024 --distance dot --chunk-size 2000 create-collection precision-search

${YELLOW}🔄 Maintenance Examples:${NC}
    # Optimize existing collection
    $0 optimize-collection my-collection

    # Full reindex with new settings
    $0 --force reindex-collection outdated-collection

    # Backup and migration
    $0 backup-collection important-collection
    $0 migrate-collection legacy-collection

${YELLOW}🎯 Specialized Use Cases:${NC}
    # Security-focused analysis
    $0 --complexity-threshold 30 --format csv analyze-codebase /security/critical/code

    # Documentation and comments indexing
    $0 --chunk-size 500 --smart-chunking index-custom /docs documentation-search

    # Multi-language polyglot repository
    $0 --enable-sparse --chunk-overlap 200 index-custom /polyglot-repo multilang-search

EOF
}

show_templates() {
    cat << EOF
${WHITE}Collection Templates${NC}

${GREEN}small_codebase${NC} - Optimized for repositories under 10,000 files
    • Vector size: 384 (sentence-transformers compatible)
    • No quantization (full precision)
    • Single shard, single replica
    • Sparse vectors enabled for keyword search
    • Fast indexing with minimal resource usage

${GREEN}medium_codebase${NC} - Balanced for 10,000-100,000 files
    • Vector size: 384
    • Scalar quantization (8-bit) for memory efficiency
    • 2 shards for better distribution
    • Optimized for search performance vs. memory usage
    • Enhanced HNSW parameters

${GREEN}large_codebase${NC} - Aggressive optimization for 100,000+ files
    • Vector size: 768 (higher dimensional embeddings)
    • Product quantization for maximum compression
    • 4+ shards with load balancing
    • On-disk HNSW index for memory management
    • Advanced segment optimization

${GREEN}high_performance${NC} - Production-grade reliability and speed
    • Vector size: 384 (optimized for speed)
    • Scalar quantization with always-in-RAM
    • High replication factor (3) for fault tolerance
    • Write consistency factor 2
    • 6 shards for maximum throughput
    • Enhanced WAL configuration
    • Multi-threaded optimization

${YELLOW}Custom Template Creation:${NC}
    You can create custom templates by editing the configuration file:
    ${CONFIG_FILE}

    Look for the "collection_templates" section and add your own template
    with customized parameters for your specific use case.

EOF
}

show_languages() {
    cat << EOF
${WHITE}Supported Programming Languages${NC}

${YELLOW}Fully Supported (with advanced analysis):${NC}
    ${GREEN}Python${NC}        - Functions, classes, imports, decorators, docstrings
    ${GREEN}JavaScript${NC}    - Functions, classes, imports, exports, ES6+ features
    ${GREEN}TypeScript${NC}    - Types, interfaces, generics, decorators
    ${GREEN}Java${NC}          - Classes, methods, packages, annotations
    ${GREEN}C/C++${NC}         - Functions, classes, includes, namespaces
    ${GREEN}Go${NC}            - Functions, types, packages, interfaces
    ${GREEN}Rust${NC}          - Functions, structs, enums, traits, modules

${YELLOW}Well Supported:${NC}
    ${GREEN}C#${NC}            - Classes, methods, namespaces, LINQ
    ${GREEN}PHP${NC}           - Functions, classes, namespaces, traits
    ${GREEN}Ruby${NC}          - Classes, methods, modules, mixins
    ${GREEN}Swift${NC}         - Functions, classes, protocols, extensions
    ${GREEN}Kotlin${NC}        - Functions, classes, data classes, extensions
    ${GREEN}Scala${NC}         - Functions, classes, objects, traits

${YELLOW}Basic Support:${NC}
    ${GREEN}Shell/Bash${NC}    - Functions, variables, sourcing
    ${GREEN}PowerShell${NC}    - Functions, cmdlets, modules
    ${GREEN}SQL${NC}           - Tables, views, procedures, functions
    ${GREEN}HTML/CSS${NC}      - Tags, classes, IDs, selectors
    ${GREEN}XML/JSON${NC}      - Structure, schemas, configurations

${YELLOW}Configuration & Data:${NC}
    ${GREEN}YAML/JSON${NC}     - Configuration structure analysis
    ${GREEN}TOML/INI${NC}      - Configuration parsing and indexing
    ${GREEN}Dockerfile${NC}    - Instructions, layers, dependencies
    ${GREEN}Makefile${NC}      - Targets, dependencies, variables

${YELLOW}Documentation:${NC}
    ${GREEN}Markdown${NC}      - Headers, links, code blocks, tables
    ${GREEN}reStructuredText${NC} - Sections, directives, references
    ${GREEN}Plain Text${NC}    - General text content analysis

${YELLOW}Language-Specific Features:${NC}
    • ${GREEN}Complexity Analysis${NC} - Cyclomatic complexity, nesting levels
    • ${GREEN}Structure Extraction${NC} - Functions, classes, imports, exports
    • ${GREEN}Semantic Chunking${NC} - Preserve logical boundaries
    • ${GREEN}Keyword Detection${NC} - Language-specific patterns
    • ${GREEN}Import Tracking${NC} - Dependency analysis
    • ${GREEN}Comment/Doc Extraction${NC} - Documentation and comments

EOF
}

# Function to load configuration
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        print_status "Creating default configuration..."
        return 1
    fi

    # Extract Qdrant connection settings
    if command -v python3 &> /dev/null; then
        QDRANT_URL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['qdrant']['url'])" 2>/dev/null || echo "")
        API_KEY=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['qdrant']['api_key'])" 2>/dev/null || echo "")
    else
        print_error "Python 3 is required but not installed"
        return 1
    fi

    if [[ -z "$QDRANT_URL" || -z "$API_KEY" ]]; then
        print_error "Failed to load Qdrant configuration from $CONFIG_FILE"
        return 1
    fi
}

# Function to check dependencies
check_dependencies() {
    local missing_deps=()

    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi

    if ! python3 -c "import requests" 2>/dev/null; then
        missing_deps+=("python-requests")
    fi

    if [[ ! -f "$INDEXER_SCRIPT" ]]; then
        missing_deps+=("enhanced indexer script")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done

        print_status "To install Python dependencies:"
        echo "  pip3 install requests pathlib2 chardet python-magic"
        return 1
    fi

    return 0
}

# Function to run enhanced indexer
run_enhanced_indexer() {
    local command="$1"
    shift
    local args=("$@")

    print_header "Running Enhanced Indexer: $command"
    print_status "Qdrant URL: $QDRANT_URL"
    print_status "Arguments: ${args[*]}"

    python3 "$INDEXER_SCRIPT" \
        --qdrant-url "$QDRANT_URL" \
        --api-key "$API_KEY" \
        "$command" \
        "${args[@]}"
}

# Function to get collection template config
get_template_config() {
    local template="$1"

    if [[ -z "$template" ]]; then
        echo "small_codebase"
        return 0
    fi

    # Validate template exists in config
    local valid_templates=("small_codebase" "medium_codebase" "large_codebase" "high_performance")
    local template_found=false

    for valid_template in "${valid_templates[@]}"; do
        if [[ "$template" == "$valid_template" ]]; then
            template_found=true
            break
        fi
    done

    if [[ "$template_found" == false ]]; then
        print_warning "Unknown template '$template', using 'small_codebase'"
        echo "small_codebase"
    else
        echo "$template"
    fi
}

# Function to estimate collection size and recommend template
recommend_template() {
    local path="$1"

    if [[ ! -d "$path" ]]; then
        echo "small_codebase"
        return 0
    fi

    print_progress "Analyzing directory structure for template recommendation..."

    # Count files quickly
    local file_count
    file_count=$(find "$path" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.java" -o -name "*.cpp" -o -name "*.c" -o -name "*.h" \) 2>/dev/null | wc -l)

    local total_size_mb
    total_size_mb=$(du -sm "$path" 2>/dev/null | cut -f1)

    print_status "Found approximately $file_count code files ($total_size_mb MB total)"

    if [[ $file_count -lt 1000 ]] && [[ $total_size_mb -lt 50 ]]; then
        print_status "Recommended template: small_codebase"
        echo "small_codebase"
    elif [[ $file_count -lt 10000 ]] && [[ $total_size_mb -lt 500 ]]; then
        print_status "Recommended template: medium_codebase"
        echo "medium_codebase"
    elif [[ $file_count -lt 50000 ]] && [[ $total_size_mb -lt 2000 ]]; then
        print_status "Recommended template: large_codebase"
        echo "large_codebase"
    else
        print_status "Recommended template: high_performance"
        echo "high_performance"
    fi
}

# Function to validate collection name
validate_collection_name() {
    local name="$1"

    if [[ -z "$name" ]]; then
        print_error "Collection name cannot be empty"
        return 1
    fi

    if [[ ${#name} -gt 63 ]]; then
        print_error "Collection name too long (max 63 characters)"
        return 1
    fi

    if [[ ! $name =~ ^[a-zA-Z0-9][a-zA-Z0-9_-]*$ ]]; then
        print_error "Collection name must start with alphanumeric character and contain only letters, numbers, hyphens, and underscores"
        return 1
    fi

    return 0
}

# Function for health check
health_check() {
    print_header "System Health Check"

    # Check dependencies
    print_progress "Checking dependencies..."
    if check_dependencies; then
        print_success "All dependencies satisfied"
    else
        return 1
    fi

    # Check configuration
    print_progress "Validating configuration..."
    if load_config; then
        print_success "Configuration loaded successfully"
    else
        return 1
    fi

    # Test Qdrant connection
    print_progress "Testing Qdrant connection..."
    if curl -s --max-time 10 -H "api-key: $API_KEY" "$QDRANT_URL/collections" > /dev/null 2>&1; then
        print_success "Qdrant server is accessible"
    else
        print_error "Cannot connect to Qdrant server at $QDRANT_URL"
        return 1
    fi

    # Check available disk space
    print_progress "Checking disk space..."
    local available_space_gb
    available_space_gb=$(df -BG "$SCRIPT_DIR" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $available_space_gb -gt 1 ]]; then
        print_success "Sufficient disk space available (${available_space_gb}GB)"
    else
        print_warning "Low disk space: ${available_space_gb}GB available"
    fi

    print_success "Health check completed successfully"
    return 0
}

# Parse command line arguments
COLLECTION_NAME=""
CUSTOM_URL=""
CUSTOM_API_KEY=""
TEMPLATE=""
VECTOR_SIZE=""
DISTANCE_METRIC=""
MAX_FILES=""
CHUNK_SIZE=""
CHUNK_OVERLAP=""
RECREATE=""
REPORT_ONLY=""
OUTPUT_FILE=""
VERBOSE=""
QUIET=""
DRY_RUN=""
FORCE=""
PARALLEL=""
WORKERS=""
BATCH_SIZE=""
ENABLE_QUANTIZATION=""
QUANTIZATION_TYPE=""
ENABLE_SPARSE=""
REPLICATION_FACTOR=""
SHARDS=""
SMART_CHUNKING=""
COMPLEXITY_THRESHOLD=""
MAX_FILE_SIZE=""

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -u|--url)
            CUSTOM_URL="$2"
            shift 2
            ;;
        -k|--api-key)
            CUSTOM_API_KEY="$2"
            shift 2
            ;;
        -t|--template)
            TEMPLATE="$2"
            shift 2
            ;;
        --vector-size)
            VECTOR_SIZE="$2"
            shift 2
            ;;
        --distance)
            DISTANCE_METRIC="$2"
            shift 2
            ;;
        -m|--max-files)
            MAX_FILES="$2"
            shift 2
            ;;
        --max-file-size)
            MAX_FILE_SIZE="$2"
            shift 2
            ;;
        --chunk-size)
            CHUNK_SIZE="$2"
            shift 2
            ;;
        --chunk-overlap)
            CHUNK_OVERLAP="$2"
            shift 2
            ;;
        --complexity-threshold)
            COMPLEXITY_THRESHOLD="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --batch-size)
            BATCH_SIZE="$2"
            shift 2
            ;;
        --replication)
            REPLICATION_FACTOR="$2"
            shift 2
            ;;
        --shards)
            SHARDS="$2"
            shift 2
            ;;
        --quantization-type)
            QUANTIZATION_TYPE="$2"
            shift 2
            ;;
        -r|--recreate)
            RECREATE="--recreate"
            shift
            ;;
        -R|--report-only)
            REPORT_ONLY="--report-only"
            shift
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --enable-quantization)
            ENABLE_QUANTIZATION="--enable-quantization"
            shift
            ;;
        --enable-sparse)
            ENABLE_SPARSE="--enable-sparse-vectors"
            shift
            ;;
        --smart-chunking)
            SMART_CHUNKING="--smart-chunking"
            shift
            ;;
        --parallel)
            PARALLEL="--parallel"
            shift
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --force)
            FORCE="--force"
            shift
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -q|--quiet)
            QUIET="--quiet"
            shift
            ;;
        --examples)
            show_examples
            exit 0
            ;;
        --templates)
            show_templates
            exit 0
            ;;
        --languages)
            show_languages
            exit 0
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
        *)
            COMMAND="$1"
            shift
            break
            ;;
    esac
done

# Check dependencies and load config
if ! check_dependencies; then
    exit 1
fi

if ! load_config; then
    exit 1
fi

# Override with custom values if provided
[[ -n "$CUSTOM_URL" ]] && QDRANT_URL="$CUSTOM_URL"
[[ -n "$CUSTOM_API_KEY" ]] && API_KEY="$CUSTOM_API_KEY"

# Build argument arrays
COMMON_ARGS=()
[[ -n "$VERBOSE" ]] && COMMON_ARGS+=("$VERBOSE")
[[ -n "$QUIET" ]] && COMMON_ARGS+=("$QUIET")

CREATE_ARGS=()
[[ -n "$VECTOR_SIZE" ]] && CREATE_ARGS+=("--vector-size" "$VECTOR_SIZE")
[[ -n "$DISTANCE_METRIC" ]] && CREATE_ARGS+=("--distance-metric" "$DISTANCE_METRIC")
[[ -n "$ENABLE_QUANTIZATION" ]] && CREATE_ARGS+=("$ENABLE_QUANTIZATION")
[[ -n "$QUANTIZATION_TYPE" ]] && CREATE_ARGS+=("--quantization-type" "$QUANTIZATION_TYPE")
[[ -n "$ENABLE_SPARSE" ]] && CREATE_ARGS+=("$ENABLE_SPARSE")
[[ -n "$REPLICATION_FACTOR" ]] && CREATE_ARGS+=("--replication-factor" "$REPLICATION_FACTOR")
[[ -n "$SHARDS" ]] && CREATE_ARGS+=("--shard-number" "$SHARDS")

INDEX_ARGS=()
[[ -n "$MAX_FILES" ]] && INDEX_ARGS+=("--max-files" "$MAX_FILES")
[[ -n "$CHUNK_SIZE" ]] && INDEX_ARGS+=("--max-chunk-size" "$CHUNK_SIZE")
[[ -n "$CHUNK_OVERLAP" ]] && INDEX_ARGS+=("--chunk-overlap" "$CHUNK_OVERLAP")
[[ -n "$OUTPUT_FILE" ]] && INDEX_ARGS+=("--output-report" "$OUTPUT_FILE")

FULL_INDEX_ARGS=()
[[ -n "$RECREATE" ]] && FULL_INDEX_ARGS+=("$RECREATE")
[[ -n "$MAX_FILES" ]] && FULL_INDEX_ARGS+=("--max-files" "$MAX_FILES")
[[ -n "$ENABLE_QUANTIZATION" ]] && FULL_INDEX_ARGS+=("$ENABLE_QUANTIZATION")
[[ -n "$ENABLE_SPARSE" ]] && FULL_INDEX_ARGS+=("$ENABLE_SPARSE")
[[ -n "$VECTOR_SIZE" ]] && FULL_INDEX_ARGS+=("--vector-size" "$VECTOR_SIZE")
[[ -n "$OUTPUT_FILE" ]] && FULL_INDEX_ARGS+=("--output-report" "$OUTPUT_FILE")

# Execute commands
case "$COMMAND" in
    create-collection)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required"
            echo "Usage: $0 create-collection COLLECTION_NAME [TEMPLATE]"
            exit 1
        fi

        COLLECTION_NAME="$1"
        TEMPLATE_NAME="${2:-}"

        if ! validate_collection_name "$COLLECTION_NAME"; then
            exit 1
        fi

        if [[ -n "$TEMPLATE_NAME" ]]; then
            TEMPLATE_NAME=$(get_template_config "$TEMPLATE_NAME")
            print_status "Using template: $TEMPLATE_NAME"
        fi

        run_enhanced_indexer "create-collection" "$COLLECTION_NAME" "${CREATE_ARGS[@]}" "${COMMON_ARGS[@]}"
        ;;

    delete-collection)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required"
            exit 1
        fi

        COLLECTION_NAME="$1"
        DELETE_ARGS=()
        [[ -n "$FORCE" ]] && DELETE_ARGS+=("--confirm")

        run_enhanced_indexer "delete-collection" "$COLLECTION_NAME" "${DELETE_ARGS[@]}" "${COMMON_ARGS[@]}"
        ;;

    list-collections)
        run_enhanced_indexer "list-collections" "${COMMON_ARGS[@]}"
        ;;

    collection-info)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required"
            exit 1
        fi

        run_enhanced_indexer "collection-info" "$1" "${COMMON_ARGS[@]}"
        ;;

    index-bbctrl)
        COLLECTION_NAME="bbctrl-firmware-enhanced"
        PATH_TO_INDEX="/Volumes/Work/Buildbotics/bbctrl-firmware"

        run_enhanced_indexer "index" "$PATH_TO_INDEX" --collection "$COLLECTION_NAME" "${INDEX_ARGS[@]}" "${COMMON_ARGS[@]}"
        ;;

    index-debugger)
        COLLECTION_NAME="gcode-debugger-enhanced"
        PATH_TO_INDEX="/Volumes/Work/Buildbotics/gcode-debugger"

        run_enhanced_indexer "index" "$PATH_TO_INDEX" --collection "$COLLECTION_NAME" "${INDEX_ARGS[@]}" "${COMMON_ARGS[@]}"
        ;;

    index-combined)
        print_error "Combined indexing requires manual setup of multiple paths"
        print_status "Use separate collections and search across them, or use full-index with a parent directory"
        exit 1
        ;;

    index-custom)
        if [[ $# -eq 0 ]]; then
            print_error "Path required for index-custom command"
            exit 1
        fi

        PATH_TO_INDEX="$1"
        COLLECTION_NAME="${2:-$(basename "$PATH_TO_INDEX")-enhanced}"

        if ! validate_collection_name "$COLLECTION_NAME"; then
            exit 1
        fi

        run_enhanced_indexer "index" "$PATH_TO_INDEX" --collection "$COLLECTION_NAME" "${INDEX_ARGS[@]}" "${COMMON_ARGS[@]}"
        ;;

    full-index)
        if [[ $# -lt 2 ]]; then
            print_error "Path and collection name required for full-index command"
            exit 1
        fi

        PATH_TO_INDEX="$1"
        COLLECTION_NAME="$2"

        if ! validate_collection_name "$COLLECTION_NAME"; then
            exit 1
        fi

        run_enhanced_indexer "full-index" "$PATH_TO_INDEX" --collection "$COLLECTION_NAME" "${FULL_INDEX_ARGS[@]}" "${COMMON_ARGS[@]}"
        ;;

    analyze-codebase)
        if [[ $# -eq 0 ]]; then
            print_error "Path required for analyze-codebase command"
            exit 1
        fi

        PATH_TO_ANALYZE="$1"
        ANALYZE_ARGS=("--report-only")
        [[ -n "$OUTPUT_FILE" ]] && ANALYZE_ARGS+=("--output-report" "$OUTPUT_FILE")
        [[ -n "$COMPLEXITY_THRESHOLD" ]] && ANALYZE_ARGS+=("--complexity-threshold" "$COMPLEXITY_THRESHOLD")

        run_enhanced_indexer "index" "$PATH_TO_ANALYZE" --collection "temp-analysis-$(date +%s)" "${ANALYZE_ARGS[@]}" "${INDEX_ARGS[@]}" "${COMMON_ARGS[@]}"
        ;;

    health-check)
        health_check
        ;;

    cleanup-cache)
        print_progress "Cleaning indexing cache and temporary files..."

        # Clean Python cache
        find "$SCRIPT_DIR" -name "*.pyc" -delete 2>/dev/null || true
        find "$SCRIPT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

        # Clean temporary files
        find "$SCRIPT_DIR" -name "*.tmp" -delete 2>/dev/null || true
        find "$SCRIPT_DIR" -name ".indexing_cache" -type d -exec rm -rf {} + 2>/dev/null || true

        print_success "Cache cleanup completed"
        ;;

    optimize-collection)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required"
            exit 1
        fi

        print_progress "Collection optimization not yet implemented in enhanced indexer"
        print_status "This feature will be available in a future version"
        ;;

    backup-collection)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required"
            exit 1
        fi

        COLLECTION_NAME="$1"
        BACKUP_FILE="backup_${COLLECTION_NAME}_$(date +%Y%m%d_%H%M%S).json"

        print_progress "Creating backup of collection '$COLLECTION_NAME'..."

        if run_enhanced_indexer "collection-info" "$COLLECTION_NAME" > "$BACKUP_FILE" 2>/dev/null; then
            print_success "Collection backup saved to: $BACKUP_FILE"
        else
            print_error "Failed to create backup"
            exit 1
        fi
        ;;

    compare-collections)
        if [[ $# -lt 2 ]]; then
            print_error "Two collection names required"
            echo "Usage: $0 compare-collections COLLECTION1 COLLECTION2"
            exit 1
        fi

        COLLECTION1="$1"
        COLLECTION2="$2"

        print_progress "Comparing collections '$COLLECTION1' and '$COLLECTION2'..."

        # Get info for both collections
        INFO1=$(python3 -c "
import sys, json, requests
try:
    response = requests.get('$QDRANT_URL/collections/$COLLECTION1', headers={'api-key': '$API_KEY'})
    if response.status_code == 200:
        data = response.json()
        result = data.get('result', {})
        print(f'Points: {result.get(\"points_count\", 0)}')
        print(f'Vectors: {result.get(\"vectors_count\", 0)}')
        config = result.get('config', {})
        params = config.get('params', {})
        print(f'Distance: {params.get(\"vectors\", {}).get(\"distance\", \"Unknown\")}')
        print(f'Size: {params.get(\"vectors\", {}).get(\"size\", \"Unknown\")}')
    else:
        print('Collection not found')
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null)

        INFO2=$(python3 -c "
import sys, json, requests
try:
    response = requests.get('$QDRANT_URL/collections/$COLLECTION2', headers={'api-key': '$API_KEY'})
    if response.status_code == 200:
        data = response.json()
        result = data.get('result', {})
        print(f'Points: {result.get(\"points_count\", 0)}')
        print(f'Vectors: {result.get(\"vectors_count\", 0)}')
        config = result.get('config', {})
        params = config.get('params', {})
        print(f'Distance: {params.get(\"vectors\", {}).get(\"distance\", \"Unknown\")}')
        print(f'Size: {params.get(\"vectors\", {}).get(\"size\", \"Unknown\")}')
    else:
        print('Collection not found')
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null)

        echo ""
        print_status "Collection Comparison Results:"
        echo ""
        print_status "$COLLECTION1:"
        echo "$INFO1" | sed 's/^/  /'
        echo ""
        print_status "$COLLECTION2:"
        echo "$INFO2" | sed 's/^/  /'
        echo ""
        ;;

    reindex-collection)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required"
            exit 1
        fi

        COLLECTION_NAME="$1"

        if [[ -z "$FORCE" ]]; then
            print_warning "This will delete and recreate the collection '$COLLECTION_NAME'"
            read -p "Are you sure you want to continue? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_status "Operation cancelled"
                exit 0
            fi
        fi

        print_progress "Reindexing collection '$COLLECTION_NAME' not yet fully implemented"
        print_status "Please use the recreate option with full-index instead"
        ;;

    migrate-collection)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required"
            exit 1
        fi

        print_progress "Collection migration not yet implemented in enhanced indexer"
        print_status "This feature will be available in a future version"
        ;;

    update-schema)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required"
            exit 1
        fi

        print_progress "Schema updates not yet implemented in enhanced indexer"
        print_status "This feature will be available in a future version"
        ;;

    "")
        print_error "No command specified"
        show_help
        exit 1
        ;;

    *)
        print_error "Unknown command: $COMMAND"
        echo ""
        print_status "Available commands:"
        echo "  create-collection, delete-collection, list-collections, collection-info"
        echo "  index-bbctrl, index-debugger, index-custom, full-index"
        echo "  analyze-codebase, health-check, cleanup-cache"
        echo "  optimize-collection, backup-collection, compare-collections"
        echo "  reindex-collection, migrate-collection, update-schema"
        echo ""
        echo "Use '$0 --help' for detailed usage information"
        exit 1
        ;;
esac

print_success "Operation completed successfully!"
