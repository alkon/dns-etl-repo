"""
Default configurations for different environments.
These are applied programmatically, not through Pulumi.<stack>.yaml files.
"""

ENVIRONMENT_DEFAULTS = {
    "dev": {
        "aws:region": "us-east-1",
        "vpc:cidr_block": "10.10.0.0/16",
        "vpc:subnet_count": "2",
        "vpc:enable_dns_support": "true",
        "vpc:enable_dns_hostnames": "true",
        "vpc:nat_strategy": "none",  # No NAT for dev to save costs
    },
    "staging": {
        "aws:region": "us-east-1",
        "vpc:cidr_block": "10.20.0.0/16",
        "vpc:subnet_count": "2",
        "vpc:enable_dns_support": "true",
        "vpc:enable_dns_hostnames": "true",
        "vpc:nat_strategy": "single",  # Single NAT for staging
    },
    "prod": {
        "aws:region": "us-east-1",
        "vpc:cidr_block": "10.30.0.0/16",
        "vpc:subnet_count": "3",
        "vpc:enable_dns_support": "true",
        "vpc:enable_dns_hostnames": "true",
        "vpc:nat_strategy": "multi-az",  # HA NAT for production
    }
}

def get_environment_from_stack(stack_name: str) -> str:
    """Extract environment from stack name (e.g., 'dev-vpc' -> 'dev')"""
    return stack_name.split('-')[0]

def get_component_from_stack(stack_name: str) -> str:
    """Extract component from stack name (e.g., 'dev-vpc' -> 'vpc')"""
    parts = stack_name.split('-')
    return parts[1] if len(parts) > 1 else "vpc"