#!/bin/bash
# scripts/run_stack.sh
# Deploy a Pulumi stack for a given environment and component

set -euo pipefail

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <env> <component> [--yes]"
    echo "Example: $0 dev vpc"
    echo "Example: $0 prod vpc --yes  # Auto-approve"
    echo "Available components: vpc, eks, iam, oidc"
    exit 1
fi

ENV=$1
COMPONENT=$2
STACK_NAME="${ENV}-${COMPONENT}"
AUTO_APPROVE=""

# Check for auto-approve flag
if [ $# -eq 3 ] && [ "$3" == "--yes" ]; then
    AUTO_APPROVE="--yes"
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

# Change to Pulumi project directory
cd "$PROJECT_ROOT"

echo "========================================="
echo "Deploying stack: $STACK_NAME"
echo "Environment: $ENV"
echo "Component: $COMPONENT"
echo "========================================="

# Ensure stack exists
if ! pulumi stack ls 2>/dev/null | grep -q "^${STACK_NAME}"; then
    echo "Error: Stack $STACK_NAME does not exist!"
    echo "Run: ./scripts/bootstrap_env.sh $ENV $COMPONENT"
    exit 1
fi

# Select the stack
pulumi stack select "$STACK_NAME"

# Show current configuration
echo ""
echo "Current configuration:"
pulumi config

# Cost warning for NAT Gateways
if [ "$COMPONENT" == "vpc" ]; then
    NAT_STRATEGY=$(pulumi config get vpc:nat_strategy 2>/dev/null || echo "none")
    if [ "$NAT_STRATEGY" != "none" ]; then
        echo ""
        echo "⚠️  WARNING: NAT Gateway strategy is set to '$NAT_STRATEGY'"
        echo "This will create billable AWS resources:"
        echo "  - NAT Gateway: ~\$45/month per gateway"
        echo "  - Elastic IP: ~\$3.65/month per IP"
        echo ""
        if [ -z "$AUTO_APPROVE" ]; then
            read -p "Do you want to continue? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Deployment cancelled"
                exit 1
            fi
        fi
    fi
fi

# Run Pulumi update
echo ""
echo "Starting deployment..."
pulumi up $AUTO_APPROVE

# Show outputs
echo ""
echo "Stack outputs:"
pulumi stack output
