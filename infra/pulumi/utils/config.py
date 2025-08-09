import pulumi

def get_env_config(key: str, required=True):
    try:
        return pulumi.Config().require_object(key) if required else pulumi.Config().get_object(key)
    except Exception:
        return None
