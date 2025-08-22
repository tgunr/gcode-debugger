#!/bin/bash

# Indexer Launcher Script
# Convenience script to launch indexing tools from the main directory
# Usage: ./index.sh [command] [options]

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INDEXER_DIR="$SCRIPT_DIR/Indexer"

# Color codes for output - with terminal detection
if [[ -t 1 ]] && command -v tput >/dev/null 2>&1; then
    # Terminal supports colors using tput
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    PURPLE=$(tput setaf 5)
    CYAN=$(tput setaf 6)
    WHITE=$(tput setaf 7; tput bold)
    NC=$(tput sgr0) # No Color
elif [[ -t 1 ]]; then
    # Fallback to ANSI codes for terminals without tput
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    PURPLE='\033[0;35m'
    CYAN='\033[0;36m'
    WHITE='\033[1;37m'
    NC='\033[0m'
else
    # No color support (non-interactive or unsupported terminal)
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
    printf "%b[INDEXER LAUNCHER]%b %s\n" "$PURPLE" "$NC" "$1"
}

# Function to show usage
show_help() {
    printf "%bIndexer Launcher%b - Easy access to codebase indexing tools\n\n" "$WHITE" "$NC"

    printf "%bUSAGE:%b\n" "$YELLOW" "$NC"
    printf "    %s [COMMAND] [OPTIONS]\n\n" "$0"

    printf "%bCOMMANDS:%b\n" "$YELLOW" "$NC"
    printf "    %bEnhanced Indexer (Recommended):%b\n" "$GREEN" "$NC"
    printf "        enhanced [OPTIONS]              Launch enhanced indexer with options\n"
    printf "        health-check                    Run system health check\n"
    printf "        create COLLECTION [TEMPLATE]    Create new collection\n"
    printf "        index-bbctrl                    Index bbctrl-firmware\n"
    printf "        index-debugger                  Index gcode-debugger (memory-efficient)\n"
    printf "        index PATH COLLECTION           Index custom directory (auto-detects large projects)\n"
    printf "        analyze PATH                    Analyze codebase without indexing\n"
    printf "        list                           List collections\n"
    printf "        info COLLECTION                Get collection info\n"
    printf "        demo                           Run interactive demonstration\n\n"

    printf "    %bMemory-Efficient Indexer:%b\n" "$GREEN" "$NC"
    printf "        memory-efficient PATH COLLECTION  Use memory-efficient indexer directly\n\n"

    printf "    %bBasic Indexer:%b\n" "$GREEN" "$NC"
    printf "        basic [OPTIONS]                 Launch basic indexer with options\n\n"

    printf "    %bUtilities:%b\n" "$GREEN" "$NC"
    printf "        help                           Show this help\n"
    printf "        docs                           Open documentation\n"
    printf "        requirements                   Install Python requirements\n"
    printf "        config                         Edit configuration files\n\n"

    printf "%bCOMMON OPTIONS:%b\n" "$YELLOW" "$NC"
    printf "    -h, --help                         Show command-specific help\n"
    printf "    -v, --verbose                      Enable verbose output\n"
    printf "    -q, --quiet                        Quiet mode (errors only)\n\n"

    printf "%bEXAMPLES:%b\n" "$YELLOW" "$NC"
    printf "    %b# Quick start%b\n" "$GREEN" "$NC"
    printf "    %s health-check\n" "$0"
    printf "    %s index-bbctrl\n" "$0"
    printf "    %s index-debugger\n\n" "$0"

    printf "    %b# Create optimized collection%b\n" "$GREEN" "$NC"
    printf "    %s create my-project medium_codebase\n\n" "$0"

    printf "    %b# Index custom directory%b\n" "$GREEN" "$NC"
    printf "    %s index /path/to/code my-collection\n\n" "$0"

    printf "    %b# Analysis without indexing%b\n" "$GREEN" "$NC"
    printf "    %s analyze /path/to/code\n\n" "$0"

    printf "    %b# Interactive demo%b\n" "$GREEN" "$NC"
    printf "    %s demo\n\n" "$0"

    printf "    %b# Enhanced indexer with options%b\n" "$GREEN" "$NC"
    printf "    %s enhanced --smart-chunking --parallel full-index /code collection\n\n" "$0"

    printf "    %b# Basic indexer%b\n" "$GREEN" "$NC"
    printf "    %s basic index-custom /path/to/code\n\n" "$0"

    printf "%bCONFIGURATION:%b\n" "$YELLOW" "$NC"
    printf "    Configuration files are located in:\n"
    printf "      %s/enhanced_indexing_config.json\n" "$INDEXER_DIR"
    printf "      %s/indexing_config.json\n\n" "$INDEXER_DIR"

    printf "    Use '%s config' to edit them with your preferred editor.\n\n" "$0"

    printf "%bDOCUMENTATION:%b\n" "$YELLOW" "$NC"
    printf "    Detailed documentation is available in the Indexer directory:\n"
    printf "      %s/ENHANCED_INDEXING_README.md\n" "$INDEXER_DIR"
    printf "      %s/INDEXING_README.md\n" "$INDEXER_DIR"
    printf "      %s/README.md\n\n" "$INDEXER_DIR"
}

# Function to check if indexer directory exists
check_indexer_dir() {
    if [[ ! -d "$INDEXER_DIR" ]]; then
        print_error "Indexer directory not found: $INDEXER_DIR"
        print_status "The indexing tools should be in the 'Indexer' subdirectory."
        return 1
    fi
    return 0
}

# Function to install requirements
install_requirements() {
    print_header "Installing Python Requirements"

    if [[ ! -f "$INDEXER_DIR/indexing_requirements.txt" ]]; then
        print_error "Requirements file not found: $INDEXER_DIR/indexing_requirements.txt"
        return 1
    fi

    print_status "Installing requirements from indexing_requirements.txt..."
    if command -v pip3 &> /dev/null; then
        pip3 install -r "$INDEXER_DIR/indexing_requirements.txt"
        print_success "Requirements installed successfully!"
    elif command -v pip &> /dev/null; then
        pip install -r "$INDEXER_DIR/indexing_requirements.txt"
        print_success "Requirements installed successfully!"
    else
        print_error "Neither pip3 nor pip found. Please install pip first."
        return 1
    fi
}

# Function to edit configuration
edit_config() {
    print_header "Configuration Files"

    local configs=(
        "$INDEXER_DIR/enhanced_indexing_config.json:Enhanced Indexer Config"
        "$INDEXER_DIR/indexing_config.json:Basic Indexer Config"
    )

    printf "Available configuration files:\n"
    for i in "${!configs[@]}"; do
        local config_info="${configs[$i]}"
        local file_path="${config_info%:*}"
        local description="${config_info#*:}"
        printf "  %d. %s\n" "$((i+1))" "$description"
        printf "     %s\n" "$file_path"
    done

    printf "\n"
    read -p "Select config file to edit (1-${#configs[@]}): " choice

    if [[ "$choice" =~ ^[1-9][0-9]*$ ]] && [[ "$choice" -le "${#configs[@]}" ]]; then
        local selected_config="${configs[$((choice-1))]}"
        local file_path="${selected_config%:*}"

        # Try different editors
        if command -v code &> /dev/null; then
            code "$file_path"
        elif command -v vim &> /dev/null; then
            vim "$file_path"
        elif command -v nano &> /dev/null; then
            nano "$file_path"
        else
            print_warning "No suitable editor found. Opening with default system editor..."
            if command -v open &> /dev/null; then
                open "$file_path"
            elif command -v xdg-open &> /dev/null; then
                xdg-open "$file_path"
            else
                printf "Please edit: %s\n" "$file_path"
            fi
        fi
    else
        print_error "Invalid selection"
        return 1
    fi
}

# Function to open documentation
open_docs() {
    print_header "Documentation"

    local docs=(
        "$INDEXER_DIR/README.md:Main README"
        "$INDEXER_DIR/ENHANCED_INDEXING_README.md:Enhanced Indexer Guide"
        "$INDEXER_DIR/INDEXING_README.md:Basic Indexer Guide"
    )

    printf "Available documentation:\n"
    for i in "${!docs[@]}"; do
        local doc_info="${docs[$i]}"
        local file_path="${doc_info%:*}"
        local description="${doc_info#*:}"
        printf "  %d. %s\n" "$((i+1))" "$description"
        printf "     %s\n" "$file_path"
    done

    printf "\n"
    read -p "Select documentation to open (1-${#docs[@]}): " choice

    if [[ "$choice" =~ ^[1-9][0-9]*$ ]] && [[ "$choice" -le "${#docs[@]}" ]]; then
        local selected_doc="${docs[$((choice-1))]}"
        local file_path="${selected_doc%:*}"

        # Try to open with appropriate viewer
        if command -v code &> /dev/null; then
            code "$file_path"
        elif command -v open &> /dev/null; then
            open "$file_path"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "$file_path"
        else
            less "$file_path"
        fi
    else
        print_error "Invalid selection"
        return 1
    fi
}

# Main command processing
if [[ $# -eq 0 ]]; then
    show_help
    exit 0
fi

if ! check_indexer_dir; then
    exit 1
fi

COMMAND="$1"
shift

case "$COMMAND" in
    enhanced)
        print_header "Launching Enhanced Indexer"
        cd "$INDEXER_DIR"
        exec ./enhanced_index_codebase.sh "$@"
        ;;

    basic)
        print_header "Launching Basic Indexer"
        cd "$INDEXER_DIR"
        exec ./index_codebase.sh "$@"
        ;;

    health-check)
        print_header "Running Health Check"
        cd "$INDEXER_DIR"
        exec ./enhanced_index_codebase.sh health-check "$@"
        ;;

    create)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required"
            printf "Usage: %s create COLLECTION_NAME [TEMPLATE]\n" "$0"
            exit 1
        fi
        print_header "Creating Collection: $1"
        cd "$INDEXER_DIR"
        exec ./enhanced_index_codebase.sh create-collection "$@"
        ;;

    index-bbctrl)
        print_header "Indexing bbctrl-firmware"
        cd "$INDEXER_DIR"
        exec ./enhanced_index_codebase.sh index-bbctrl "$@"
        ;;

    index-debugger)
        print_header "Indexing gcode-debugger"
        print_warning "Using memory-efficient indexer due to project size"
        cd "$INDEXER_DIR"
        exec ./run_memory_efficient_indexing.sh /Volumes/Work/Buildbotics/gcode-debugger --collection gcode-debugger-enhanced --batch-size 25 --max-files 2000 --max-file-size 5 --skip-qdrant-check "$@"
        ;;

    index)
        if [[ $# -lt 2 ]]; then
            print_error "Path and collection name required"
            printf "Usage: %s index PATH COLLECTION\n" "$0"
            exit 1
        fi
        print_header "Indexing Custom Directory: $1"
        print_status "Checking project size to determine indexer..."
        PROJECT_PATH="$1"
        COLLECTION="$2"
        shift 2

        # Check if project is large (>500MB or >5000 files)
        if [[ -d "$PROJECT_PATH" ]]; then
            FILE_COUNT=$(find "$PROJECT_PATH" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.json" -o -name "*.md" \) | wc -l | tr -d ' ')
            if [[ "$FILE_COUNT" -gt 5000 ]]; then
                print_warning "Large project detected ($FILE_COUNT files). Using memory-efficient indexer."
                cd "$INDEXER_DIR"
                exec ./run_memory_efficient_indexing.sh "$PROJECT_PATH" --collection "$COLLECTION" --batch-size 25 --max-files 3000 --max-file-size 5 "$@"
            fi
        fi

        cd "$INDEXER_DIR"
        exec ./enhanced_index_codebase.sh index-custom "$PROJECT_PATH" "$COLLECTION" "$@"
        ;;

    analyze)
        if [[ $# -eq 0 ]]; then
            print_error "Path required"
            printf "Usage: %s analyze PATH\n" "$0"
            exit 1
        fi
        print_header "Analyzing Codebase: $1"
        cd "$INDEXER_DIR"
        exec ./enhanced_index_codebase.sh analyze-codebase "$@"
        ;;

    list)
        print_header "Listing Collections"
        cd "$INDEXER_DIR"
        exec ./enhanced_index_codebase.sh list-collections "$@"
        ;;

    info)
        if [[ $# -eq 0 ]]; then
            print_error "Collection name required"
            printf "Usage: %s info COLLECTION_NAME\n" "$0"
            exit 1
        fi
        print_header "Collection Information: $1"
        cd "$INDEXER_DIR"
        exec ./enhanced_index_codebase.sh collection-info "$@"
        ;;

    demo)
        print_header "Running Interactive Demo"
        cd "$INDEXER_DIR"
        if [[ -f "demo_enhanced_indexing.py" ]]; then
            exec python3 demo_enhanced_indexing.py "$@"
        else
            print_error "Demo script not found"
            exit 1
        fi
        ;;

    help|--help|-h)
        show_help
        ;;

    docs)
        open_docs
        ;;

    config)
        edit_config
        ;;

    requirements)
        install_requirements
        ;;

    memory-efficient)
        if [[ $# -lt 2 ]]; then
            print_error "Path and collection name required"
            printf "Usage: %s memory-efficient PATH COLLECTION\n" "$0"
            exit 1
        fi
        print_header "Using Memory-Efficient Indexer: $1"
        cd "$INDEXER_DIR"
        exec ./run_memory_efficient_indexing.sh "$1" --collection "$2" "${@:3}"
        ;;

    *)
        print_error "Unknown command: $COMMAND"
        printf "\n"
        print_status "Available commands:"
        printf "  enhanced, basic, health-check, create, index-bbctrl, index-debugger\n"
        printf "  index, analyze, list, info, demo, memory-efficient, help, docs, config, requirements\n"
        printf "\n"
        printf "Use '%s help' for detailed usage information\n" "$0"
        exit 1
        ;;
esac
