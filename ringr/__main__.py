import sys
import argparse
from pathlib import Path
import logging

from .config import load_config
from .notifiers import create_notifier
from .audio import AudioDetector


log = logging.getLogger('ringr')


DEFAULT_CONFIG_FILE = '/etc/ringr/ringr.conf'


def configure_logger(verbose: bool):
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    log.addHandler(handler)


def parse_args():
    parser = argparse.ArgumentParser(description='ringr. Sound event detection system')
    parser.add_argument('-c', '--conf', help='Configuration file', metavar='file',
                        default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-v', '--verbose', help='Show debug log messages in the log', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    configure_logger(args.verbose)

    try:
        config = load_config(Path(args.conf))
        notifier = create_notifier(config.notifier)
        detector = AudioDetector(config.detector, notifier)

        log.info('Starting detector')

        detector.start()

    except (KeyboardInterrupt, SystemExit):
        # Do nothing
        pass

    except Exception:
        log.error('Something went wrong', exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
