#!/usr/bin/python3.7
import argparse
import sys

from rolling import verbose, basic, Mode


def parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Perform a roll, in a syntax that is an extension of D&D's. "
                                                 "The most basic of this type of roll is the '1d20', just a die roll. "
                                                 "More complex may include addition or subtraction of modifiers or "
                                                 "other die rolls. All common arithmetic operations are supported so "
                                                 "knock yourself out.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('-a', '--average', action='store_true',
                      help='calculate the average of the given roll')
    mode.add_argument('-c', '--critical', action='store_true',
                      help='roll the dice as a critical hit (roll twice as many)')
    mode.add_argument('-m', '--maximum', action='store_true',
                      help='calculate the maximum value that can be rolled')

    parser.add_argument('-n', '--number', default=1, type=int,
                        help='roll each expression this many times')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='roll in verbose mode, showing the results of each dice roll')
    parser.add_argument('-w', '--wrap', default=80, type=int,
                        help='wrap lines after this many characters. 0 for no wrapping')
    parser.add_argument('expression', nargs='+',
                        help='the rolling expressions to be performed')
    return parser.parse_args(sys.argv[1:])


def main():
    args = parse()
    mode = Mode.NORMAL
    if args.average:
        mode = Mode.AVERAGE
    elif args.critical:
        mode = Mode.CRIT
    elif args.maximum:
        mode = Mode.MAX
    func = basic
    if args.verbose:
        func = verbose

    for expr in args.expression:
        length = 0
        for each in range(args.number):
            val = func(expr, mode)
            s = f"{val} "
            length += len(s)
            if length > args.wrap:
                print()
                length = len(s)
            print(s, end="")
        print()


if __name__ == '__main__':
    main()
