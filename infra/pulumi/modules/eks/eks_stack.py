import pulumi
import pulumi_aws as aws
import pulumi_eks as eks
from common.config_loader import load_config

def run(env):
    config = load_config(env)

    cluster = eks.Cluster("eksCluster",
        role_arn=config["eks"]["role_arn"],
        vpc_id=config["eks"]["vpc_id"],
        public_subnet_ids=config["eks"]["public_subnet_ids"],
        private_subnet_ids=config["eks"]["private_subnet_ids"],
        skip_default_node_group=True)

    pulumi.export("kubeconfig", cluster.kubeconfig)
