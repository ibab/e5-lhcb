import logging
logger = logging.getLogger(__name__)

from .log import setup_logging
from .util import setup_roofit
from .config import get_args, get_config

def main():
    args = get_args()
    setup_logging()
    setup_roofit()

    config = get_config()
    args.func(config, args)

