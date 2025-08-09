import pulumi
import pulumi_aws as aws
from typing import List

class SubnetGroup(pulumi.ComponentResource):
    """Manages a group of subnets (public or private)"""
    
    def __init__(self, name: str, vpc_id: pulumi.Output[str], args: dict, opts=None):
        super().__init__('custom:vpc:SubnetGroup', name, None, opts)
        
        self.subnets: List[aws.ec2.Subnet] = []
        subnet_type = args.get("type", "public")
        environment = args.get("environment", "dev")
        
        # Get availability zones
        azs = aws.get_availability_zones(state="available")
        
        # Create subnets
        for i in range(args.get("count", 2)):
            if i >= len(azs.names):
                break
                
            # Calculate subnet CIDR
            base_cidr = args.get("base_cidr_prefix", "10.0")
            cidr_offset = args.get("cidr_offset", 0)
            subnet_cidr = f"{base_cidr}.{cidr_offset + i}.0/24"
            
            # EKS-specific tags
            eks_tags = {}
            if subnet_type == "public":
                eks_tags["kubernetes.io/role/elb"] = "1"
            else:
                eks_tags["kubernetes.io/role/internal-elb"] = "1"
            
            subnet = aws.ec2.Subnet(f"{name}-{i+1}",
                vpc_id=vpc_id,
                cidr_block=subnet_cidr,
                availability_zone=azs.names[i],
                map_public_ip_on_launch=(subnet_type == "public"),
                tags={
                    "Name": f"{name}-{i+1}",
                    "Environment": environment,
                    "Type": subnet_type,
                    **eks_tags
                },
                opts=pulumi.ResourceOptions(parent=self))
            
            self.subnets.append(subnet)
        
        self.register_outputs({
            "subnet_ids": [s.id for s in self.subnets],
            "subnet_cidrs": [s.cidr_block for s in self.subnets]
        })