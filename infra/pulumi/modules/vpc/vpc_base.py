import pulumi
import pulumi_aws as aws

class VpcBase(pulumi.ComponentResource):
    """Base VPC with only free resources (VPC, IGW, Route Tables)"""
    
    def __init__(self, name: str, args: dict, opts=None):
        super().__init__('custom:vpc:VpcBase', name, None, opts)
        
        self.vpc = aws.ec2.Vpc(f"{name}-vpc",
            cidr_block=args.get("cidr_block", "10.0.0.0/16"),
            enable_dns_support=args.get("enable_dns_support", True),
            enable_dns_hostnames=args.get("enable_dns_hostnames", True),
            tags={
                "Name": f"{name}-vpc",
                "Environment": args.get("environment", "dev"), # fallback default
                "ManagedBy": "Pulumi"
            },
            opts=pulumi.ResourceOptions(parent=self))
        
        # Internet Gateway (free resource)
        self.igw = aws.ec2.InternetGateway(f"{name}-igw",
            vpc_id=self.vpc.id,
            tags={
                "Name": f"{name}-igw",
                "Environment": args.get("environment", "dev")
            },
            opts=pulumi.ResourceOptions(parent=self))
        
        # Public Route Table (free resource)
        self.public_route_table = aws.ec2.RouteTable(f"{name}-public-rt",
            vpc_id=self.vpc.id,
            tags={
                "Name": f"{name}-public-rt",
                "Environment": args.get("environment", "dev")
            },
            opts=pulumi.ResourceOptions(parent=self))
        
        # Default route to IGW (free)
        self.public_route = aws.ec2.Route(f"{name}-public-route",
            route_table_id=self.public_route_table.id,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=self.igw.id,
            opts=pulumi.ResourceOptions(parent=self))
        
        self.register_outputs({
            "vpc_id": self.vpc.id,
            "vpc_cidr": self.vpc.cidr_block,
            "igw_id": self.igw.id,
            "public_route_table_id": self.public_route_table.id
        })