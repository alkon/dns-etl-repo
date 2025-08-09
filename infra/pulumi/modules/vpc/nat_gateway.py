import pulumi
import pulumi_aws as aws
from typing import List

class NatGatewayGroup(pulumi.ComponentResource):
    """NAT Gateways and EIPs - PAID RESOURCES
    
    WARNING: This creates billable resources:
    - Elastic IPs: ~$3.65/month each when associated
    - NAT Gateways: ~$45/month each + data transfer costs
    
    For dev/test environments, consider using a single NAT instance or 
    NAT Gateway in one AZ only to reduce costs.
    """
    
    def __init__(self, name: str, public_subnet_ids: List[pulumi.Output[str]], 
                 vpc_id: pulumi.Output[str], args: dict, opts=None):
        super().__init__('custom:vpc:NatGatewayGroup', name, None, opts)
        
        self.nat_gateways = []
        self.eips = []
        self.private_route_tables = []
        
        # Determine NAT Gateway strategy
        strategy = args.get("strategy", "single")  # single, multi-az, or none
        environment = args.get("environment", "dev")
        
        if strategy == "none":
            pulumi.log.info("NAT Gateway strategy is 'none' - skipping NAT Gateway creation")
            return
        
        # For single NAT strategy, use only first subnet
        subnet_count = 1 if strategy == "single" else len(public_subnet_ids)
        
        for i in range(subnet_count):
            # Allocate Elastic IP
            eip = aws.ec2.Eip(f"{name}-nat-eip-{i+1}",
                domain="vpc",
                tags={
                    "Name": f"{name}-nat-eip-{i+1}",
                    "Environment": environment,
                    "CostCenter": "networking"
                },
                opts=pulumi.ResourceOptions(parent=self))
            self.eips.append(eip)
            
            # Create NAT Gateway
            nat = aws.ec2.NatGateway(f"{name}-nat-{i+1}",
                subnet_id=public_subnet_ids[i],
                allocation_id=eip.id,
                tags={
                    "Name": f"{name}-nat-{i+1}",
                    "Environment": environment,
                    "CostCenter": "networking"
                },
                opts=pulumi.ResourceOptions(parent=self))
            self.nat_gateways.append(nat)
        
        # Create private route tables
        # For single NAT, all private subnets use the same NAT
        private_subnet_count = args.get("private_subnet_count", 2)
        
        for i in range(private_subnet_count):
            # Determine which NAT to use
            nat_index = 0 if strategy == "single" else min(i, len(self.nat_gateways) - 1)
            
            private_rt = aws.ec2.RouteTable(f"{name}-private-rt-{i+1}",
                vpc_id=vpc_id,
                tags={
                    "Name": f"{name}-private-rt-{i+1}",
                    "Environment": environment
                },
                opts=pulumi.ResourceOptions(parent=self))
            
            # Add route to NAT Gateway
            aws.ec2.Route(f"{name}-private-route-{i+1}",
                route_table_id=private_rt.id,
                destination_cidr_block="0.0.0.0/0",
                nat_gateway_id=self.nat_gateways[nat_index].id,
                opts=pulumi.ResourceOptions(parent=self))
            
            self.private_route_tables.append(private_rt)
        
        # Calculate monthly cost estimate
        eip_cost = len(self.eips) * 3.65
        nat_cost = len(self.nat_gateways) * 45
        total_cost = eip_cost + nat_cost
        
        pulumi.log.warn(f"NAT Gateway estimated monthly cost: ${total_cost:.2f} " +
                       f"(EIPs: ${eip_cost:.2f}, NAT Gateways: ${nat_cost:.2f})")
        
        self.register_outputs({
            "nat_gateway_ids": [n.id for n in self.nat_gateways],
            "eip_ids": [e.id for e in self.eips],
            "private_route_table_ids": [rt.id for rt in self.private_route_tables],
            "estimated_monthly_cost": total_cost
        })