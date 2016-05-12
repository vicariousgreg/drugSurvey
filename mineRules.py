#!/usr/bin/python2
#
# Authors:      Greg Davis
#               Daniel Kauffman
# Assignment:   Lab 6
# Course:       CPE 466
# Instructor:   A. Dekhtyar
# Term:         Fall 2015

from __future__ import print_function
import argparse
import csv
import math
import random
import sys

from associationRules import Dataset


def main():
    args = set_options()
    if args.verbose:
        print("Options:", str(vars(args)))

    with open(args.goods, "r") as goodsfile:
        goods = [line.strip() for line in goodsfile.readlines()]

    with open(args.csvfile, "r") as csvfile:
        lines = [line for line in csv.reader(csvfile) if len(line) > 0]
        dataset = Dataset(lines, args.minSup)

        itemsets = dataset.apriori(skyline = not args.all, verbose=args.verbose)
        for s in itemsets: 
            if len(s.items) > 1:
                print(s.tostring(goods))

        print("=" * 80)
        rules = dataset.genRules(args.minConf, skyline=not args.all, verbose=args.verbose)
        for rule in rules:
            print(rule.tostring(goods))
        print("=" * 80)
        print("%d frequent item sets and %d rules found." % (len(itemsets), len(rules)))


def set_options():
    """
    Retrieve the user-entered arguments for the program.
    """
    parser = argparse.ArgumentParser(description = 
    """Perform association rules mining on a given data set.""")
    parser.add_argument("csvfile", help = 
    """the comma-separated values file with data on which to perform 
       rule mining""")
    parser.add_argument("goods", help = 
    """the file containing names for item indices""")
    parser.add_argument("minSup", type = float, help = 
    """minimum support for frequent itemsets""")
    parser.add_argument("minConf", type = float, help = 
    """minimum confidence for rules""")
    parser.add_argument('-a', '--all', dest='all', action='store_true',
                        help = 
    """Includes all item sets, not just skyline.""")
    parser.add_argument("-v", "--verbose", action = "store_true", help = 
    """print additional information to the terminal as the program is 
       executing""")
    return parser.parse_args()

if __name__ == "__main__":
    main()


