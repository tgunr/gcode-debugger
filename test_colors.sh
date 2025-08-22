#!/bin/bash

# Color Test Script
# Tests different methods of displaying colors in the terminal

echo "=== Color Output Test ==="
echo ""

# Method 1: Direct ANSI codes with echo -e
echo "Method 1: Direct ANSI codes with echo -e"
echo -e "\033[0;31mRed text\033[0m"
echo -e "\033[0;32mGreen text\033[0m"
echo -e "\033[1;33mYellow text\033[0m"
echo -e "\033[0;34mBlue text\033[0m"
echo ""

# Method 2: ANSI codes with printf
echo "Method 2: ANSI codes with printf"
printf "\033[0;31mRed text\033[0m\n"
printf "\033[0;32mGreen text\033[0m\n"
printf "\033[1;33mYellow text\033[0m\n"
printf "\033[0;34mBlue text\033[0m\n"
echo ""

# Method 3: Using printf with %b format specifier
echo "Method 3: printf with %b format specifier"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

printf "%bRed text%b\n" "$RED" "$NC"
printf "%bGreen text%b\n" "$GREEN" "$NC"
printf "%bYellow text%b\n" "$YELLOW" "$NC"
printf "%bBlue text%b\n" "$BLUE" "$NC"
echo ""

# Method 4: Using tput (if available)
echo "Method 4: Using tput (if available)"
if command -v tput >/dev/null 2>&1; then
    RED_TPUT=$(tput setaf 1)
    GREEN_TPUT=$(tput setaf 2)
    YELLOW_TPUT=$(tput setaf 3)
    BLUE_TPUT=$(tput setaf 4)
    NC_TPUT=$(tput sgr0)

    printf "%sRed text%s\n" "$RED_TPUT" "$NC_TPUT"
    printf "%sGreen text%s\n" "$GREEN_TPUT" "$NC_TPUT"
    printf "%sYellow text%s\n" "$YELLOW_TPUT" "$NC_TPUT"
    printf "%sBlue text%s\n" "$BLUE_TPUT" "$NC_TPUT"
else
    echo "tput command not available"
fi
echo ""

# Method 5: Test terminal detection
echo "Method 5: Terminal detection results"
if [[ -t 1 ]]; then
    echo "✓ stdout is connected to a terminal"
else
    echo "✗ stdout is NOT connected to a terminal (redirected or piped)"
fi

if command -v tput >/dev/null 2>&1; then
    echo "✓ tput command is available"
    echo "  Terminal type: $(tput longname 2>/dev/null || echo 'unknown')"
    echo "  Colors supported: $(tput colors 2>/dev/null || echo 'unknown')"
else
    echo "✗ tput command is NOT available"
fi

if [[ -n "$TERM" ]]; then
    echo "✓ TERM environment variable is set: $TERM"
else
    echo "✗ TERM environment variable is NOT set"
fi

if [[ -n "$COLORTERM" ]]; then
    echo "✓ COLORTERM environment variable is set: $COLORTERM"
else
    echo "✗ COLORTERM environment variable is NOT set"
fi

echo ""
echo "=== Test Complete ==="
echo "If you see colors above, your terminal supports color output."
echo "If you see escape sequences like \\033[0;31m, colors are not supported or not enabled."
