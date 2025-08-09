import pulumi
import pulumi_aws as aws
from .vpc_base import VpcBase
from .subnets import SubnetGroup
from .nat_gateway import NatGatewayGroup
from config.defaults import ENVIRONMENT_DEFAULTS, get_environment_from_stack

def run(env: str):
    """Main VPC stack that orchestrates all VPC components"""
    
    # Get configuration using Pulumi's config system
    config = pulumi.Config()
    stack = pulumi.get_stack()
    
    # Get environment defaults
    env_defaults = ENVIRONMENT_DEFAULTS.get(env, {})
    
    # Helper function to get config with environment defaults
    def get_config(key: str, default=None):
        """Get config value with fallback to environment defaults"""
        value = config.get(key)
        if value is None:
            # Remove namespace prefix for lookup in defaults
            default_key = key.replace("vpc:", "vpc:")
            value = env_defaults.get(default_key, default)
        return value
    
    def get_config_bool(key: str, default=False):
        """Get boolean config value with fallback to environment defaults"""
        value = config.get_bool(key)
        if value is None:
            default_key = key.replace("vpc:", "vpc:")
            default_value = env_defaults.get(default_key, str(default)).lower()
            value = default_value == "true"
        return value
    
    def get_config_int(key: str, default=0):
        """Get integer config value with fallback to environment defaults"""
        value = config.get_int(key)
        if value is None:
            default_key = key.replace("vpc:", "vpc:")
            value = int(env_defaults.get(default_key, str(default)))
        return value
    
    # VPC configuration with defaults
    vpc_name = get_config("vpc:name") or f"{env}-vpc"
    vpc_cidr = get_config("vpc:cidr_block", "10.0.0.0/16")
    
    # Subnet configuration
    subnet_count = get_config_int("vpc:subnet_count", 2)
    
    # NAT Gateway configuration (IMPORTANT: These are paid resources!)
    nat_strategy = get_config("vpc:nat_strategy", "none")  # none, single, multi-az
    
    # Log configuration source
    pulumi.log.info(f"Loading configuration for environment: {env}")
    pulumi.log.info(f"VPC CIDR: {vpc_cidr} (from {'config' if config.get('vpc:cidr_block') else 'defaults'})")
    pulumi.log.info(f"NAT Strategy: {nat_strategy} (from {'config' if config.get('vpc:nat_strategy') else 'defaults'})")
    
    # Determine CIDR prefix based on environment
    cidr_prefix_map = {
        "dev": "10.10",
        "staging": "10.20", 
        "prod": "10.30"
    }
    base_cidr_prefix = cidr_prefix_map.get(env, "10.0")
    
    # 1. Create base VPC (free resources only)
    vpc_base = VpcBase(vpc_name, {
        "cidr_block": vpc_cidr,
        "environment": env,
        "enable_dns_support": get_config_bool("vpc:enable_dns_support", True),
        "enable_dns_hostnames": get_config_bool("vpc:enable_dns_hostnames", True)
    })
    
    # 2. Create public subnets
    public_subnets = SubnetGroup(f"{vpc_name}-public", 
        vpc_base.vpc.id,
        {
            "type": "public",
            "count": subnet_count,
            "environment": env,
            "base_cidr_prefix": base_cidr_prefix,
            "cidr_offset": 0  # Start at .0.0/24, .1.0/24, etc.
        })
    
    # Associate public subnets with public route table
    for i, subnet_id in enumerate(public_subnets.subnets):
        aws.ec2.RouteTableAssociation(f"{vpc_name}-public-rta-{i+1}",
            subnet_id=subnet_id.id,
            route_table_id=vpc_base.public_route_table.id)
    
    # 3. Create private subnets
    private_subnets = SubnetGroup(f"{vpc_name}-private",
        vpc_base.vpc.id,
        {
            "type": "private", 
            "count": subnet_count,
            "environment": env,
            "base_cidr_prefix": base_cidr_prefix,
            "cidr_offset": 100  # Start at .100.0/24, .101.0/24, etc.
        })
    
    # 4. Conditionally create NAT Gateways (PAID RESOURCES)
    nat_group = None
    if nat_strategy != "none":
        pulumi.log.warn(f"Creating NAT Gateways with strategy '{nat_strategy}' - these are PAID resources!")
        
        nat_group = NatGatewayGroup(vpc_name,
            [s.id for s in public_subnets.subnets],
            vpc_base.vpc.id,
            {
                "strategy": nat_strategy,
                "environment": env,
                "private_subnet_count": subnet_count
            })
        
        # Associate private subnets with NAT route tables
        for i, subnet in enumerate(private_subnets.subnets):
            if i < len(nat_group.private_route_tables):
                aws.ec2.RouteTableAssociation(f"{vpc_name}-private-rta-{i+1}",
                    subnet_id=subnet.id,
                    route_table_id=nat_group.private_route_tables[i].id)
    else:
        pulumi.log.info("NAT Gateway strategy is 'none' - private subnets will have no internet access")
        pulumi.log.info("To enable NAT, set vpc:nat_strategy to 'single' (dev) or 'multi-az' (prod)")
    
    # Export outputs
    pulumi.export("vpc_id", vpc_base.vpc.id)
    pulumi.export("vpc_cidr", vpc_base.vpc.cidr_block)
    pulumi.export("internet_gateway_id", vpc_base.igw.id)
    pulumi.export("public_subnet_ids", public_subnets.subnet_ids)
    pulumi.export("private_subnet_ids", private_subnets.subnet_ids)
    
    if nat_group:
        pulumi.export("nat_gateway_ids", nat_group.nat_gateway_ids)
        pulumi.export("nat_gateway_monthly_cost_estimate", nat_group.estimated_monthly_cost)
    else:
        pulumi.export("nat_gateway_ids", [])
        pulumi.export("nat_gateway_monthly_cost_estimate", 0)
    
    # Export configuration info
    pulumi.export("nat_strategy", nat_strategy)
    pulumi.export("environment", env)
