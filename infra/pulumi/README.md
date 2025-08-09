# Multi-Environment AWS Infrastructure with Pulumi

This project provides a modular, cost-optimized approach to deploying AWS infrastructure using Pulumi with Python.

## Architecture

The project follows Pulumi best practices with:
- **Modular components** - Separate modules for VPC, subnets, NAT gateways, etc.
- **Cost optimization** - NAT Gateways and other paid resources are optional
- **Multi-environment support** - Dev, staging, and production configurations
- **Infrastructure as Code** - All infrastructure defined in Python

## Project Structure

```
infra/pulumi/
├── __main__/__init__.py      # Main entry point with stack dispatcher
├── common/                   # Shared utilities
│   └── stack_utils.py       # Dynamic stack routing
├── modules/                  # Infrastructure modules
│   ├── vpc/                 # VPC module
│   │   ├── vpc_stack.py    # Main VPC orchestrator
│   │   ├── vpc_base.py     # Base VPC (free resources)
│   │   ├── subnets.py      # Subnet management
│   │   └── nat_gateway.py  # NAT Gateway (paid resource)
│   ├── eks/                 # EKS module (future)
│   ├── iam/                 # IAM module
│   └── oidc/                # OIDC module
├── scripts/                  # Helper scripts
│   ├── bootstrap_env.sh     # Initialize Pulumi stacks
│   └── run_stack.sh         # Deploy stacks
└── Pulumi.*.yaml            # Stack configurations
```

## Cost Considerations

### Free Resources
- VPC
- Internet Gateway
- Route Tables
- Subnets
- Security Groups

### Paid Resources (Optional)
- **NAT Gateway**: ~$45/month per gateway + data transfer
- **Elastic IP**: ~$3.65/month when associated with NAT Gateway

The project allows you to deploy without NAT Gateways for development to save costs.

## Prerequisites

1. **AWS Account and Credentials**
   ```bash
   aws configure --profile dev-profile
   aws configure --profile staging-profile
   aws configure --profile prod-profile
   ```

2. **Pulumi CLI**
   ```bash
   # Install Pulumi CLI (if not already installed)
   curl -fsSL https://get.pulumi.com | sh
   
   # Or via Homebrew on macOS
   brew install pulumi
   ```

3. **Pulumi Account**
   ```bash
   # Login to Pulumi (uses local backend by default)
   pulumi login
   
   # Or login to Pulumi Cloud
   pulumi login https://app.pulumi.com
   ```

4. **Python 3.8+**
   ```bash
   python --version
   ```

5. **Install Python Dependencies**
   ```bash
   cd infra/pulumi
   
   # Create virtual environment (recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

## Configuration Strategy

This project follows Pulumi best practices:

1. **No `Pulumi.<stack>.yaml` files in source control** - These files should be managed by Pulumi Service/backend
2. **Environment defaults in code** - Default configurations are defined in `config/defaults.py`
3. **Override via CLI** - Use `pulumi config set` to override any defaults
4. **Secrets management** - Use `pulumi config set --secret` for sensitive values

## Quick Start

### 1. Setup Environment

```bash
cd infra/pulumi

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Initialize a Stack

```bash
   ./scripts/bootstrap_env.sh dev vpc # Bootstrap the stack (still in infra/pulumi directory)
```

### 3. Configure AWS Profile

```bash
   pulumi config set aws:profile dev-profile # Set your AWS profile (required)
```

### 4. Review Default Configuration

Default configurations are automatically applied based on environment:
- **Dev**: No NAT Gateway (free), 10.10.0.0/16 CIDR
- **Staging**: Single NAT Gateway, 10.20.0.0/16 CIDR  
- **Prod**: Multi-AZ NAT Gateways, 10.30.0.0/16 CIDR

To see current configuration:
```bash
pulumi config
```

### 5. Override Defaults (Optional)

```bash
   pulumi config set vpc:nat_strategy single # Change NAT strategy
   pulumi config set vpc:cidr_block 10.15.0.0/16 # Change CIDR block
   pulumi config set vpc:subnet_count 3 # Change subnet count
```

### 6. Deploy the Stack

```bash
   pulumi preview --stack dev-vpc # Preview changes
   ./scripts/run_stack.sh dev vpc # Deploy
   ./scripts/run_stack.sh dev vpc --yes # Auto-approve deployment
```

## NAT Gateway Strategies

### 1. None (Free)
```yaml
vpc:nat_strategy: none
```
- No NAT Gateways deployed
- Private subnets have no internet access
- Perfect for development or when using VPC endpoints

### 2. Single NAT (Cost-Optimized)
```yaml
vpc:nat_strategy: single
```
- One NAT Gateway for all availability zones
- ~$45/month + data transfer
- Good for dev/staging environments

### 3. Multi-AZ NAT (High Availability)
```yaml
vpc:nat_strategy: multi-az
```
- One NAT Gateway per availability zone
- ~$45/month per AZ + data transfer
- Recommended for production

## Common Commands

### Stack Management
```bash
   pulumi stack ls # List all stacks
   pulumi stack select dev-vpc # Select a stack
   pulumi config # Show stack configuration
   pulumi stack output # Show stack outputs
```

### Update NAT Strategy
```bash
   pulumi config set vpc:nat_strategy single --stack dev-vpc # Change NAT strategy for existing stack
   pulumi up --stack dev-vpc
```

### Bulk Configuration (Optional)
While we use environment defaults in code, you can use `pulumi config set-all` for specific scenarios:

```bash
   ./scripts/apply-config.sh dev-vpc configs/my-overrides.yaml # Apply bulk configuration from YAML file
```

This is useful for:
- Team-shared configuration templates
- Temporary testing configurations  
- Migrating from other systems

### Destroy Resources
```bash
   pulumi destroy --stack dev-vpc # Destroy all resources in a stack
```

## GitHub Actions

The project includes a GitHub Actions workflow for automated deployments:

1. Go to Actions tab in GitHub
2. Select "Deploy VPC with Pulumi"
3. Click "Run workflow"
4. Choose environment and NAT strategy
5. Review and approve deployment

### Required Secrets
- `PULUMI_ACCESS_TOKEN`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## Troubleshooting

### Common Issues

1. **AWS Profile Not Found**
   ```bash
   # Update the profile in Pulumi config
   pulumi config set aws:profile your-profile-name
   ```

2. **Stack Already Exists**
   ```bash
      pulumi stack select dev-vpc # Select existing stack instead of creating
   ```

3. **Subnet CIDR Conflicts**
   - Ensure different CIDR blocks for each environment
   - Dev: 10.10.0.0/16
   - Staging: 10.20.0.0/16
   - Prod: 10.30.0.0/16

## Next Steps

1. **Add EKS Support**
   - The VPC is already tagged for EKS compatibility
   - Subnets include required Kubernetes tags

2. **VPC Peering**
   - Connect VPCs across environments if needed

3. **VPC Endpoints**
   - Add S3, ECR endpoints to reduce NAT Gateway costs

## Best Practices

### Configuration Management

This project follows Pulumi's recommended configuration approach:

**Why no `Pulumi.<stack>.yaml` files?**
1. **Security**: Prevents accidental commit of secrets
2. **Flexibility**: Each developer can have their own config without conflicts
3. **Pulumi Service Integration**: Works seamlessly with Pulumi Service config management
4. **Environment Parity**: Defaults ensure consistency across environments

**Benefits of this approach:**
- Configurations are stored in Pulumi's backend (local or cloud)
- Sensitive values are encrypted automatically
- Easy to share stacks with team members
- No merge conflicts from config files

### Cost Optimization

1. **Start with Free Resources**
   - Deploy with `nat_strategy: none` first
   - Add NAT Gateways only when needed

2. **Use Cost Alerts**
   - Set up AWS billing alerts
   - Monitor NAT Gateway data transfer

3. **Environment Isolation**
   - Use separate AWS accounts for prod
   - Different CIDR ranges per environment

4. **Regular Reviews**
   - Check for unused resources
   - Review NAT Gateway metrics

## Support

For issues or questions:
1. Check Pulumi logs: `pulumi logs --stack dev-vpc`
2. Review AWS CloudFormation events in console
3. Open an issue in the repository