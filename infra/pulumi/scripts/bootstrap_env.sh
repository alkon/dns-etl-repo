#!/bin/bash
# scripts/bootstrap_env.sh
# Bootstrap a new Pulumi stack for a given environment

set -euo pipefail

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <env> <component> [--apply-defaults]"
    echo "Example: $0 dev vpc"
    echo "Example: $0 dev vpc --apply-defaults"
    echo "Available components: vpc, eks, iam, oidc"
    echo "Available environments: dev, staging, prod"
    exit 1
fi

ENV=$1
COMPONENT=$2
STACK_NAME="${ENV}-${COMPONENT}"
APPLY_DEFAULTS=false

# Check for apply-defaults flag
if [ $# -eq 3 ] && [ "$3" == "--apply-defaults" ]; then
    APPLY_DEFAULTS=true
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."

# Change to Pulumi project directory
cd "$PROJECT_ROOT"

echo "========================================="
echo "Bootstrapping stack: $STACK_NAME"
echo "Environment: $ENV"
echo "Component: $COMPONENT"
echo "========================================="

# Initialize stack if it doesn't exist
if ! pulumi stack ls 2>/dev/null | grep -q "^${STACK_NAME}"; then
    echo "Creating new stack: $STACK_NAME"
    pulumi stack init "$STACK_NAME"
else
    echo "Stack $STACK_NAME already exists"
fi

# Select the stack
pulumi stack select "$STACK_NAME"

# Note about configuration
echo ""
echo "📝 Configuration Strategy:"
echo "- Default values are built into the code for each environment"
echo "- You can override any default using: pulumi config set <key> <value>"
echo "- Sensitive values should be set with: pulumi config set --secret <key> <value>"
echo ""

# Show current configuration
echo "Current configuration:"
pulumi config

# List common configuration options
echo ""
echo "Common configuration options you might want to override:"
echo "  pulumi config set aws:profile <your-aws-profile>"
echo "  pulumi config set vpc:nat_strategy <none|single|multi-az>"
echo "  pulumi config set vpc:cidr_block <cidr>"
echo ""

# AWS Profile reminder
if ! pulumi config get aws:profile 2>/dev/null; then
    echo "⚠️  WARNING: No AWS profile configured!"
    echo "Set your AWS profile with:"
    echo "  pulumi config set aws:profile <your-profile-name>"
    echo ""
fi

echo "Stack $STACK_NAME is ready!"
echo ""
echo "Next steps:"
echo "1. Set your AWS profile: pulumi config set aws:profile <profile-name>"
echo "2. Review/modify configuration: pulumi config"
echo "3. Deploy: ./scripts/run_stack.sh $ENV $COMPONENT"
