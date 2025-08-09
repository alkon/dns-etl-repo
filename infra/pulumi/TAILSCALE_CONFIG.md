# Tailscale VPC Configuration Guide

## Overview

This document outlines how Tailscale simplifies our AWS VPC architecture, reduces costs, and provides secure networking without traditional VPN/NAT Gateway complexity.

## Architecture Simplification

### What Tailscale Replaces

| Component | Traditional Cost | With Tailscale | Savings |
|-----------|-----------------|----------------|---------|
| NAT Gateways | $45/month each + data | Not needed | $45-135/month |
| VPN Gateway | $36/month + connection fees | Tailscale is the VPN | $36/month |
| Bastion Hosts | EC2 instance costs | Direct SSH via Tailscale | Variable |
| Complex Security Groups | Management overhead | Simplified with ACLs | Time/complexity |
| Elastic IPs (for NAT) | $3.65/month each | Not needed | $3.65-11/month |
| Transit Gateway | $0.05/hour + data | Tailscale mesh networking | ~$36/month |
| Site-to-Site VPN | $0.05/hour per connection | Replaced by Tailscale | ~$36/month |
| VPC Peering (cross-region) | Data transfer costs | Tailscale handles it | Variable |
| Customer Gateway | Configuration complexity | Not needed | Time saved |

### Total Cost Savings

- **Development**: ~$540/year (single NAT + EIP)
- **Staging**: ~$540/year (single NAT + EIP)
- **Production**: ~$1,620/year (multi-AZ NAT + EIPs)
- **Multi-region**: Additional ~$432/year per Transit Gateway

## Simplified VPC Architecture

### Traditional VPC Requirements
```yaml
vpc:
  cidr_block: 10.10.0.0/16
  nat_strategy: single    # Or multi-az for HA
  subnet_count: 2
  # Results in: IGW, NAT Gateways, Route Tables, EIPs
```

### With Tailscale
```yaml
vpc:
  cidr_block: 10.10.0.0/16
  nat_strategy: none      # No NAT needed!
  subnet_count: 2
  enable_tailscale: true
  tailscale_auth_key: "tskey-auth-xxxxx"  # From Tailscale admin
```

## VPC Modules That Can Be Removed

### Completely Remove These Modules
1. **nat_gateway.py** - Entire module not needed ($45-135/month savings)
2. **Private route tables for NAT** - No NAT means no private routes needed
3. **VPN Gateway modules** - Tailscale replaces all VPN functionality
4. **Transit Gateway modules** - Tailscale provides mesh networking
5. **Customer Gateway configs** - Not needed with Tailscale
6. **VPC Endpoint modules** - Reduced need (Tailscale handles connectivity)

### Simplified Modules
1. **Security Groups** - Only minimal SGs for ALB/public access needed
2. **Network ACLs** - Can rely more on Tailscale ACLs
3. **Route Tables** - Only public routes needed
4. **VPC Peering** - Tailscale handles cross-VPC connectivity

## Components Still Needed

Even with Tailscale, you still need:

1. **VPC and Subnets** - Basic network isolation
2. **Internet Gateway** - For ALB/public services only
3. **Public Subnets** - For load balancers
4. **Private Subnets** - For EKS nodes/EC2 instances (but simplified)
5. **Minimal Security Groups** - For ALB ingress
6. **OIDC Provider** - Still needed for EKS IRSA (and it's free!)

## Free AWS Components

### OIDC Provider (No Cost)
The OIDC provider for EKS IRSA is completely free:
- **Creating OIDC provider**: $0
- **Storing OIDC provider**: $0
- **Authentication requests**: $0
- **Token exchanges**: $0

This remains unchanged with Tailscale since it handles identity, not networking.

## EKS Integration

### Node Configuration

Tailscale integrates with EKS without custom CNI plugins:

1. **AWS VPC CNI** - Handles pod networking (unchanged)
2. **Tailscale Operator** - Runs as DaemonSet on nodes
3. **Node-to-Node** - Traffic encrypted via Tailscale
4. **External Access** - Through Tailscale network
5. **No Custom CNI** - Tailscale complements, doesn't replace CNI

### Implementation Methods

#### Option 1: UserData Installation (Recommended for EC2)
```bash
#!/bin/bash
# Add to EKS node group launch template
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --auth-key=${TAILSCALE_AUTH_KEY} --accept-routes
```

#### Option 2: Tailscale Operator (Recommended for EKS)
```yaml
# Deploy via Helm
helm repo add tailscale https://pkgs.tailscale.com/helmcharts
helm install tailscale-operator tailscale/tailscale-operator \
  --set-string oauth.clientId="${CLIENT_ID}" \
  --set-string oauth.clientSecret="${CLIENT_SECRET}"
```

## Benefits

### Security
- **Zero-trust networking** - All connections authenticated
- **End-to-end encryption** - WireGuard protocol
- **Simplified ACLs** - Replace complex security groups
- **No public IPs** - Instances only accessible via Tailscale

### Operations
- **Direct SSH access** - No bastion/jump hosts
- **Simple kubectl** - Direct cluster access
- **Unified access control** - Single ACL system
- **Cross-region connectivity** - Built-in mesh networking

### Cost
- **No egress fees** - Package downloads via Tailscale
- **No NAT charges** - Biggest savings
- **Reduced data transfer** - Optimized routing
- **Simplified architecture** - Lower operational overhead

## Shadow Deployments with Tailscale

### Recommended Tool: Flagger

Flagger works seamlessly with Tailscale because:
- No service mesh required
- Works with basic Kubernetes networking
- Supports progressive delivery
- Lightweight and simple

### Installation
```bash
# Add Flagger Helm repository
helm repo add flagger https://flagger.app

# Install Flagger
helm upgrade -i flagger flagger/flagger \
  --namespace=flagger-system \
  --create-namespace \
  --set meshProvider=kubernetes \
  --set prometheus.install=true
```

### Shadow Deployment Configuration
```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: my-app
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  service:
    port: 80
    targetPort: 8080
    trafficPolicy:
      tls:
        mode: DISABLE  # Tailscale handles encryption
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    webhooks:
    - name: shadow-test
      type: pre-rollout
      url: http://flagger-loadtester.test/
      metadata:
        type: shadow
```

### Alternative: Argo Rollouts
If you prefer Argo Rollouts:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app-rollout
spec:
  strategy:
    canary:
      trafficRouting:
        nginx:
          stableIngress: my-app-stable
      steps:
      - setMirrorRoute:
          name: my-app-preview
          percentage: 100
          duration: 10m
```

## Implementation Checklist

### Phase 1: VPC Setup
- [ ] Deploy VPC with `nat_strategy: none`
- [ ] Create public/private subnets
- [ ] Configure Internet Gateway for ALB only
- [ ] Set up minimal security groups

### Phase 2: Tailscale Integration
- [ ] Create Tailscale auth keys
- [ ] Add to Pulumi config as secrets
- [ ] Configure node userdata/operator
- [ ] Test connectivity

### Phase 3: EKS/EC2 Deployment
- [ ] Deploy nodes without public IPs
- [ ] Install Tailscale on nodes
- [ ] Configure subnet routing if needed
- [ ] Test kubectl access

### Phase 4: Shadow Deployments (Optional)
- [ ] Install Flagger
- [ ] Configure canary resources
- [ ] Set up metrics collection
- [ ] Test shadow traffic

## Configuration Reference

### Environment Variables
```bash
# Required
export TAILSCALE_AUTH_KEY="tskey-auth-xxxxx"

# Optional
export TAILSCALE_HOSTNAME="${INSTANCE_ID}"
export TAILSCALE_ADVERTISE_ROUTES="10.10.0.0/16"
```

### Pulumi Configuration
```bash
# Set Tailscale auth key
pulumi config set --secret tailscale:authKey "tskey-auth-xxxxx"

# Enable Tailscale in VPC
pulumi config set vpc:enable_tailscale true

# Disable NAT Gateway
pulumi config set vpc:nat_strategy none
```

### Security Group Rules
With Tailscale, you only need:
```yaml
# ALB Security Group
ingress:
  - protocol: tcp
    from_port: 80
    to_port: 80
    cidr_blocks: ["0.0.0.0/0"]
  - protocol: tcp
    from_port: 443
    to_port: 443
    cidr_blocks: ["0.0.0.0/0"]

# Node Security Group
ingress:
  - protocol: tcp
    from_port: 41641  # Tailscale
    to_port: 41641
    cidr_blocks: ["0.0.0.0/0"]
```

## Troubleshooting

### Common Issues

1. **Nodes can't reach internet**
   - Verify Tailscale is running: `tailscale status`
   - Check exit node configuration
   - Ensure subnet routes are advertised

2. **kubectl timeout**
   - Verify Tailscale connectivity to cluster
   - Check if API server endpoint is accessible
   - Ensure proper ACLs in Tailscale admin

3. **Shadow deployment not working**
   - Verify Flagger webhook connectivity
   - Check ingress controller configuration
   - Ensure metrics server is accessible

## Tools That Excel with Tailscale

### 1. Karpenter (Node Autoscaling)
Karpenter works exceptionally well with Tailscale:
```yaml
# Karpenter provisioner with Tailscale
userData: |
  #!/bin/bash
  curl -fsSL https://tailscale.com/install.sh | sh
  tailscale up --auth-key=${TAILSCALE_AUTH_KEY} --accept-routes
```
- Auto-provisions nodes with Tailscale pre-installed
- No NAT Gateway needed for node downloads
- Spot instances connect seamlessly
- Simplified node bootstrapping

### 2. Teleport (Advanced Access Control)
- Complements Tailscale's networking with advanced RBAC
- Session recording and audit logs
- Works over Tailscale connections
- No bastion hosts needed

### 3. Development Tools
**Tilt** - Local Kubernetes development
- Direct cluster access without port-forwarding
- Live reload over secure connection
- Team collaboration simplified

**Skaffold** - CI/CD pipeline
- Deploy directly to private clusters
- No exposed endpoints needed

### 4. Observability Stack
**Prometheus + Grafana**
- Metrics stay on private network
- Federated monitoring over Tailscale
- No public dashboards

**Vector** - Log aggregation
- Ship logs securely without public endpoints
- Reduced egress costs
- Built-in encryption via Tailscale

### 5. GitOps Tools
**ArgoCD**
- Access UI securely via Tailscale
- No public ingress required
- Multi-cluster management simplified

**Flux**
- Webhook receivers on private network
- Secure git sync

### 6. Service Mesh Alternatives
Instead of complex service meshes, use:
- **Tailscale** for encryption and identity
- **Flagger** for progressive delivery
- **Linkerd** (if needed) - lightweight option

### Integration Benefits
1. **Security**: Everything stays on private network
2. **Cost**: No public load balancers or endpoints
3. **Simplicity**: Direct connectivity without complexity
4. **Performance**: Optimized routing via Tailscale mesh

## Summary of Simplifications

### Infrastructure Changes
- **Remove**: nat_gateway.py module entirely
- **Remove**: VPN Gateway, Transit Gateway, Customer Gateway modules
- **Simplify**: Security groups to only what's needed for ALB
- **Simplify**: Route tables (only public routes needed)
- **Keep**: OIDC provider (free and required for IRSA)
- **Keep**: Basic VPC components (vpc_base.py, subnets.py)

### Cost Impact
- **Immediate savings**: $45-135/month from NAT Gateways
- **Additional savings**: ~$72/month if replacing VPN/Transit Gateways
- **Data transfer savings**: Reduced AWS egress charges
- **Total potential savings**: $2,000-4,000/year depending on architecture

## Resources

- [Tailscale Kubernetes Operator](https://tailscale.com/kb/1236/kubernetes-operator/)
- [Flagger Documentation](https://docs.flagger.app/)
- [AWS VPC Best Practices](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-best-practices.html)
- [Tailscale ACL Documentation](https://tailscale.com/kb/1018/acls/)
- [EKS with Tailscale Guide](https://tailscale.com/kb/1115/kubernetes/)