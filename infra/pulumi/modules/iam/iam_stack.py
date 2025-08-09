import pulumi
import pulumi_aws as aws
import json
from typing import Dict, List

def run(env: str):
    """Main IAM stack for creating users and policies"""
    
    config = pulumi.Config()
    stack = pulumi.get_stack()
    
    # Check if user already exists by trying to get it
    existing_user = None
    user_name = f"pulumi-{env}-user"
    
    try:
        # Try to import existing user
        existing_user = aws.iam.get_user(user_name=user_name)
        pulumi.log.info(f"User {user_name} already exists")
    except:
        pulumi.log.info(f"User {user_name} does not exist, will create it")
    
    # Create IAM user for Pulumi operations in this environment
    user = aws.iam.User(f"{env}-pulumi-user",
        name=user_name,
        tags={
            "Environment": env,
            "ManagedBy": "Pulumi",
            "Purpose": "Infrastructure provisioning"
        })
    
    # Create access key for the user
    access_key = aws.iam.AccessKey(f"{env}-pulumi-access-key",
        user=user.name)
    
    # Define policies for VPC management
    vpc_policy_document = aws.iam.get_policy_document(statements=[
        {
            "sid": "VPCManagement",
            "effect": "Allow",
            "actions": [
                "ec2:DescribeAvailabilityZones",
                "ec2:DescribeVpcs",
                "ec2:CreateVpc",
                "ec2:DeleteVpc",
                "ec2:ModifyVpcAttribute",
                "ec2:DescribeVpcAttribute",
                "ec2:DescribeInternetGateways",
                "ec2:CreateInternetGateway",
                "ec2:DeleteInternetGateway",
                "ec2:AttachInternetGateway",
                "ec2:DetachInternetGateway",
                "ec2:DescribeSubnets",
                "ec2:CreateSubnet",
                "ec2:DeleteSubnet",
                "ec2:ModifySubnetAttribute",
                "ec2:DescribeRouteTables",
                "ec2:CreateRouteTable",
                "ec2:DeleteRouteTable",
                "ec2:CreateRoute",
                "ec2:DeleteRoute",
                "ec2:ReplaceRoute",
                "ec2:AssociateRouteTable",
                "ec2:DisassociateRouteTable",
                "ec2:DescribeSecurityGroups",
                "ec2:CreateSecurityGroup",
                "ec2:DeleteSecurityGroup",
                "ec2:AuthorizeSecurityGroupIngress",
                "ec2:AuthorizeSecurityGroupEgress",
                "ec2:RevokeSecurityGroupIngress",
                "ec2:RevokeSecurityGroupEgress",
                "ec2:CreateTags",
                "ec2:DeleteTags",
                "ec2:DescribeTags",
                "ec2:DescribeNatGateways",
                "ec2:CreateNatGateway",
                "ec2:DeleteNatGateway",
                "ec2:AllocateAddress",
                "ec2:ReleaseAddress",
                "ec2:DescribeAddresses",
                "ec2:AssociateAddress",
                "ec2:DisassociateAddress"
            ],
            "resources": ["*"]
        }
    ])
    
    # Create VPC management policy
    vpc_policy = aws.iam.Policy(f"{env}-vpc-policy",
        name=f"{env}-vpc-management-policy",
        description=f"Policy for managing VPCs in {env} environment",
        policy=vpc_policy_document.json)
    
    # Attach the policy to the user
    vpc_policy_attachment = aws.iam.UserPolicyAttachment(f"{env}-vpc-policy-attachment",
        user=user.name,
        policy_arn=vpc_policy.arn)
    
    # Additional policies for EKS (future use)
    if config.get_bool("iam:enable_eks_permissions"):
        eks_policy_document = aws.iam.get_policy_document(statements=[
            {
                "sid": "EKSManagement",
                "effect": "Allow",
                "actions": [
                    "eks:*",
                    "iam:CreateRole",
                    "iam:DeleteRole",
                    "iam:GetRole",
                    "iam:ListRoles",
                    "iam:AttachRolePolicy",
                    "iam:DetachRolePolicy",
                    "iam:GetRolePolicy",
                    "iam:PutRolePolicy",
                    "iam:DeleteRolePolicy",
                    "iam:ListRolePolicies",
                    "iam:CreateServiceLinkedRole",
                    "iam:PassRole"
                ],
                "resources": ["*"]
            }
        ])
        
        eks_policy = aws.iam.Policy(f"{env}-eks-policy",
            name=f"{env}-eks-management-policy",
            description=f"Policy for managing EKS in {env} environment",
            policy=eks_policy_document.json)
        
        eks_policy_attachment = aws.iam.UserPolicyAttachment(f"{env}-eks-policy-attachment",
            user=user.name,
            policy_arn=eks_policy.arn)
    
    # Export outputs
    pulumi.export("iam_user_name", user.name)
    pulumi.export("iam_user_arn", user.arn)
    
    # Export access key (marked as secret)
    pulumi.export("access_key_id", pulumi.Output.secret(access_key.id))
    pulumi.export("secret_access_key", pulumi.Output.secret(access_key.secret))
    
    # Export instructions for using the credentials
    pulumi.export("setup_instructions", pulumi.Output.all(access_key.id, user.name).apply(
        lambda args: f"""
To use these credentials:

1. Configure AWS CLI profile:
   aws configure --profile {env}-pulumi
   AWS Access Key ID: [Run 'pulumi stack output access_key_id --show-secrets' to see]
   AWS Secret Access Key: [Run 'pulumi stack output secret_access_key --show-secrets' to see]
   Default region: us-east-1
   Default output format: json

2. Update VPC stack to use this profile:
   pulumi config set aws:profile {env}-pulumi --stack {env}-vpc

User ARN: {args[1]}
"""))