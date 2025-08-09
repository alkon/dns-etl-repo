#!/bin/bash
# scripts/apply-config.sh
# Optional utility to bulk-apply configuration from YAML files
# Use case: Team-shared config templates or migration from old setups

set -euo pipefail

if [ $# -ne 2 ]; then
    echo "Usage: $0 <stack-name> <config-file>"
    echo "Example: $0 dev-vpc configs/dev-vpc-overrides.yaml"
    exit 1
fi

STACK_NAME=$1
CONFIG_FILE=$2

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

cd "$PROJECT_ROOT"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file $CONFIG_FILE not found"
    exit 1
fi

echo "Applying configuration from $CONFIG_FILE to stack $STACK_NAME"

# Select stack
pulumi stack select "$STACK_NAME"

# Apply all configs from YAML
pulumi config set-all --path "$CONFIG_FILE"

echo "Configuration applied successfully!"
pulumi config