import importlib
from pulumi import get_stack

# Dynamically dispatch to the correct stack module
def dispatch_stack():
    stack = get_stack()  # e.g., "dev-vpc" or "dev-eks"
    env, component = stack.split('-')  # "dev", "vpc"
    module_path = f"modules.{component}.{component}_stack"
    module = importlib.import_module(module_path)
    module.run(env)  # Pass environment name like "dev"
