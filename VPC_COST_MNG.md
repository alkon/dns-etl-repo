# VPC Cost Management Guide

## Free VPC Components

| Component               | Notes                                                    |
| ----------------------- | -------------------------------------------------------- |
| VPC itself              | No cost for creating or using a VPC                      |
| Subnets                 | Public or private — free                                 |
| Route Tables            | Free to create and associate                             |
| Security Groups         | Free unless attached to resources that incur costs       |
| Network ACLs            | Free                                                     |
| Internet Gateway        | Free to attach; only costs arise from downstream traffic |
| VPC Peering             | Free (intra-region); data transfer may cost separately   |
| VPC Endpoints (Gateway) | Free (e.g., S3, DynamoDB) unless data transferred        |

## When VPC Starts to Cost You

| Trigger Component          | Cost Notes                                                              |
| -------------------------- | ----------------------------------------------------------------------- |
| NAT Gateway                | **\$0.045/hour** (~$32/month) + data processing — **very expensive**    |
| EC2 Instances              | Charged by instance type, region, hours                                 |
| Load Balancers (ALB/NLB)   | Per hour + per LCU or connection                                        |
| Elastic IP (EIP)           | Free **only when attached**; idle EIP = \~\$0.005/hour (~$3.65/month)   |
| VPN Gateway / Site-to-Site | Per hour + per connection                                               |
| Interface Endpoints        | \$ per hour + data transfer                                             |
| Traffic Data Transfer      | Cross-AZ or inter-region — **costly**, especially for public IP traffic |
| Transit Gateway            | Hourly + data processed                                                 |

## NAT Gateway Cost Breakdown

### Monthly Costs (US East 1)
- **NAT Gateway**: ~$32.40/month per gateway (24h × 30d × $0.045)
- **Elastic IP**: ~$3.65/month when attached to NAT
- **Data Processing**: $0.045 per GB processed

### Cost by Strategy
| Strategy | NAT Gateways | Monthly Cost | Use Case |
|----------|--------------|--------------|----------|
| none | 0 | $0 | Development, VPC endpoints only |
| single | 1 | ~$36 | Dev/Staging with internet needs |
| multi-az | 2-3 | ~$72-108 | Production high availability |

## Implementation in This Project

The Pulumi configuration uses a `nat_strategy` parameter to control costs:

```python
# In config/defaults.py
ENVIRONMENT_DEFAULTS = {
    "dev": {
        "vpc:nat_strategy": "none",      # Free - no NAT
    },
    "staging": {
        "vpc:nat_strategy": "single",    # ~$36/month
    },
    "prod": {
        "vpc:nat_strategy": "multi-az",  # ~$72-108/month
    }
}
```

### Override NAT Strategy

```bash
# Check current strategy
pulumi config get vpc:nat_strategy

# Change strategy (example: enable single NAT for dev)
pulumi config set vpc:nat_strategy single

# Deploy the change
pulumi up
```

## Cost Optimization Tips

1. **Development Environment**
   - Use `nat_strategy: none` and VPC endpoints instead
   - Or use a bastion host for occasional access

2. **Staging Environment**
   - Single NAT Gateway is usually sufficient
   - Schedule NAT deletion during off-hours if possible

3. **Production Environment**
   - Multi-AZ NAT for high availability
   - Monitor data transfer costs closely
   - Consider VPC endpoints for S3, ECR, etc.

4. **Data Transfer Optimization**
   - Keep traffic within the same AZ when possible
   - Use VPC endpoints for AWS services
   - Consider AWS PrivateLink for SaaS services
