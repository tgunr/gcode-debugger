#!/bin/bash

# Codebase Indexer - Convenience script for indexing codebases into Qdrant
# Usage: ./index_codebase.sh [options]

set -e

# Default configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/indexing_config.json"
INDEXER_SCRIPT="$SCRIPT_DIR/codebase_indexer.py"

# Color codes for output - with terminal detection
if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
    # Terminal supports colors
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    NC=$(tput sgr0) # No Color
elif [[ -t 1 ]]; then
    # Fallback to ANSI codes
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    # No color support
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
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

# Function to show usage
show_help() {
    cat << EOF
Codebase Indexer - Index your codebase into Qdrant vector database

USAGE:
    $0 [OPTIONS] COMMAND

COMMANDS:
    index-bbctrl        Index bbctrl-firmware codebase
    index-debugger      Index gcode-debugger codebase
    index-combined      Index both codebases into combined collection
    index-custom PATH   Index custom directory path
    list-collections    List existing Qdrant collections
    delete COLLECTION   Delete a specific collection
    info COLLECTION     Get information about a collection

OPTIONS:
    -c, --config FILE       Use custom config file (default: indexing_config.json)
    -n, --collection NAME   Override collection name
    -u, --url URL          Override Qdrant URL
    -k, --api-key KEY      Override API key
    -m, --max-files NUM    Maximum files to index
    -r, --recreate         Delete and recreate collection
    -R, --report-only      Generate report only, don't create collection
    -o, --output FILE      Output report file
    -v, --verbose          Verbose output
    -h, --help             Show this help

EXAMPLES:
    # Index bbctrl-firmware with default settings
    $0 index-bbctrl

    # Index with custom collection name
    $0 -n "my-firmware-v2" index-bbctrl

    # Generate report only (don't create collection)
    $0 -R index-debugger

    # Index custom directory with limited files
    $0 -m 100 index-custom /path/to/my/project

    # Recreate existing collection
    $0 -r index-combined

    # List all collections
    $0 list-collections

CONFIGURATION:
    Edit $CONFIG_FILE to customize:
    - Qdrant connection settings
    - File types to include/exclude
    - Indexing parameters
    - Collection definitions

EOF
}

# Function to load config
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_error "Config file not found: $CONFIG_FILE"
        exit 1
    fi

    # Extract values from JSON config using basic tools
    QDRANT_URL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['qdrant']['url'])" 2>/dev/null || echo "")
    API_KEY=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['qdrant']['api_key'])" 2>/dev/null || echo "")

    if [[ -z "$QDRANT_URL" || -z "$API_KEY" ]]; then
        print_error "Failed to load Qdrant configuration from $CONFIG_FILE"
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        print_error "python3 is required but not installed"
        exit 1
    fi

    if ! python3 -c "import requests" 2>/dev/null; then
        print_error "Python 'requests' module is required. Install with: pip3 install requests"
        exit 1
    fi

    if [[ ! -f "$INDEXER_SCRIPT" ]]; then
        print_error "Indexer script not found: $INDEXER_SCRIPT"
        exit 1
    fi
}

# Function to run indexer
run_indexer() {
    local path="$1"
    local collection="$2"
    local extra_args=("${@:3}")

    print_status "Starting indexing process..."
    print_status "Path: $path"
    print_status "Collection: $collection"
    print_status "Qdrant URL: $QDRANT_URL"

    python3 "$INDEXER_SCRIPT" \
        "$path" \
        --qdrant-url "$QDRANT_URL" \
        --api-key "$API_KEY" \
        --collection "$collection" \
        "${extra_args[@]}"
}

# Function to list collections
list_collections() {
    print_status "Fetching collections from $QDRANT_URL..."

    local response
    response=$(curl -s -H "api-key: $API_KEY" "$QDRANT_URL/collections" 2>/dev/null)

    if [[ $? -eq 0 ]]; then
        echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'result' in data and 'collections' in data['result']:
        collections = data['result']['collections']
        if collections:
            print('\\nExisting Collections:')
            for i, col in enumerate(collections, 1):
                name = col.get('name', 'Unknown')
                print(f'  {i}. {name}')
        else:
            print('No collections found.')
    else:
        print('Unexpected response format')
except Exception as e:
    print(f'Error parsing response: {e}')
"
    else
        print_error "Failed to connect to Qdrant server"
        exit 1
    fi
}

# Function to get collection info
get_collection_info() {
    local collection="$1"
    print_status "Getting information for collection: $collection"

    local response
    response=$(curl -s -H "api-key: $API_KEY" "$QDRANT_URL/collections/$collection" 2>/dev/null)

    if [[ $? -eq 0 ]]; then
        echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f'Error: {e}')
"
    else
        print_error "Failed to get collection info"
        exit 1
    fi
}

# Function to delete collection
delete_collection() {
    local collection="$1"
    print_warning "This will delete collection: $collection"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deleting collection: $collection"
        curl -s -X DELETE -H "api-key: $API_KEY" "$QDRANT_URL/collections/$collection"
        print_success "Collection deleted"
    else
        print_status "Operation cancelled"
    fi
}

# Parse command line arguments
COLLECTION_NAME=""
CUSTOM_URL=""
CUSTOM_API_KEY=""
MAX_FILES=""
RECREATE=""
REPORT_ONLY=""
OUTPUT_FILE=""
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -n|--collection)
            COLLECTION_NAME="$2"
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
        -m|--max-files)
            MAX_FILES="$2"
            shift 2
            ;;
        -r|--recreate)
            RECREATE="--recreate-collection"
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
        -v|--verbose)
            VERBOSE="true"
            shift
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

# Check dependencies
check_dependencies

# Load configuration
load_config

# Override with custom values if provided
[[ -n "$CUSTOM_URL" ]] && QDRANT_URL="$CUSTOM_URL"
[[ -n "$CUSTOM_API_KEY" ]] && API_KEY="$CUSTOM_API_KEY"

# Build extra arguments
EXTRA_ARGS=()
[[ -n "$MAX_FILES" ]] && EXTRA_ARGS+=("--max-files" "$MAX_FILES")
[[ -n "$RECREATE" ]] && EXTRA_ARGS+=("$RECREATE")
[[ -n "$REPORT_ONLY" ]] && EXTRA_ARGS+=("$REPORT_ONLY")
[[ -n "$OUTPUT_FILE" ]] && EXTRA_ARGS+=("--output-report" "$OUTPUT_FILE")

# Execute commands
case "$COMMAND" in
    index-bbctrl)
        COLLECTION="${COLLECTION_NAME:-bbctrl-firmware-codebase}"
        PATH_TO_INDEX="/Volumes/Work/Buildbotics/bbctrl-firmware"
        run_indexer "$PATH_TO_INDEX" "$COLLECTION" "${EXTRA_ARGS[@]}"
        ;;

    index-debugger)
        COLLECTION="${COLLECTION_NAME:-gcode-debugger-codebase}"
        PATH_TO_INDEX="/Volumes/Work/Buildbotics/gcode-debugger"
        run_indexer "$PATH_TO_INDEX" "$COLLECTION" "${EXTRA_ARGS[@]}"
        ;;

    index-combined)
        print_error "Combined indexing not yet implemented. Use separate collections for now."
        exit 1
        ;;

    index-custom)
        if [[ $# -eq 0 ]]; then
            print_error "Path required for index-custom command"
            show_help
            exit 1
        fi
        PATH_TO_INDEX="$1"
        COLLECTION="${COLLECTION_NAME:-$(basename "$PATH_TO_INDEX")-codebase}"
        run_indexer "$PATH_TO_INDEX" "$COLLECTION" "${EXTRA_ARGS[@]}"
        ;;

    list-collections)
        list_collections
        ;;

    info)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required for info command"
            exit 1
        fi
        get_collection_info "$1"
        ;;

    delete)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required for delete command"
            exit 1
        fi
        delete_collection "$1"
        ;;

    "")
        print_error "No command specified"
        show_help
        exit 1
        ;;

    *)
        print_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
