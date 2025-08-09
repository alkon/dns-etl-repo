import pulumi
import pulumi_aws as aws
from utils.config import get_env_config

def configure_oidc_provider():
    cfg = get_env_config("oidc")
    issuer_url = cfg.get("issuer_url")
    if not issuer_url:
        raise Exception("OIDC issuer_url must be set in config")

    oidc = aws.iam.OpenIdConnectProvider("eks-oidc",
        client_id_list=["sts.amazonaws.com"],
        thumbprint_list=["9e99a48a9960b14926bb7f3b02e22da0afd4e3e5"],
        url=issuer_url)

    pulumi.export("oidc_provider_arn", oidc.arn)
    # pulumi.export("oidc_provider_url", oidc.url)  // ???

    return oidc
