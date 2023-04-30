# main.py
# this will be what each machine runs

from synfony.common.machine import start

import argparse


def make_parser():
    """Makes a parser for command line arguments (i.e. machine addresses).
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--machines', type=list, required=True)
    return parser


def parse_args():
    """Parse the command line arguments (i.e. host and port).

        Returns: an `argparse.Namespace` (filtering out `None` values).
    """
    parser = make_parser()
    return argparse.Namespace(**{(k if k != 'machines' else
                                  'other_machine_addresses'):
                                 (v if k != 'machines' else
                                  [tuple(*v.split(':'))])
                                 for k, v in
                                 parser.parse_args().__dict__.items()
                                 if v is not None})


if __name__ == '__main__':
    start(**parse_args().__dict__)
