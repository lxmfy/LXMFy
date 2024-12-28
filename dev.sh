#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print section header
print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1 passed${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 failed${NC}"
        return 1
    fi
}

# Variable to track overall status
FAILED=0

# Format code with black
print_header "Running Black formatter"
poetry run black lxmfy
if ! check_status "Black"; then
    FAILED=1
fi

# Run pylint (allowing it to fail)
print_header "Running Pylint"
poetry run pylint lxmfy
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠ Pylint found some issues${NC}"
fi

# Run bandit security checks
print_header "Running Bandit security checks"
poetry run bandit -r lxmfy
if ! check_status "Bandit"; then
    FAILED=1
fi

# Final status
if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All critical checks passed!${NC}"
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠ Note: Pylint reported some issues that should be reviewed${NC}"
    fi
else
    echo -e "\n${RED}✗ Some checks failed!${NC}"
    exit 1
fi 