import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pulumi import get_stack
from common.stack_utils import dispatch_stack

dispatch_stack()