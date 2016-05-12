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

def candidateGen(prev, k):
    candidates = []

    # Iterate over all sets.
    for i in xrange(len(prev)):
        # Inner loop only through succeeding sets.
        for j in xrange(i+1, len(prev)):
            union = prev[i].union(prev[j])
            # Determine if union is the right size.
            if len(union) == k and union not in candidates:
                # Ensure that all subsets of size k-1 are in the previous set.
                if all(union.difference([item]) in prev for item in union):
                    # If so, add the itemset as a candidate.
                    candidates.append(union)
    return candidates

class ItemSet:
    def __init__(self, items):
        self.items = set(items)
        self.support = None

    def __repr__(self):
        items = [str(x) for x in sorted(self.items)]
        return "[%s]  (%f)" % (" ".join(items), self.support)
    def __iter__(self): return iter(self.items)
    def __len__(self): return len(self.items)
    def __eq__(self, other): return self.items == other.items

    def tostring(self, goods, stats=True):
        out = "%s" % (";".join(goods[item] for item in self.items))
        if stats:
            out += ",%f" % (self.support)
        return out

    def union(self, other):
        return ItemSet(self.items.union(other.items))
    def difference(self, toRemove):
        return ItemSet(self.items.difference(toRemove))
    def issubset(self, other):
        return self.items.issubset(other.items)

class AssociationRule:
    def __init__(self, left, right):
        self.left = ItemSet(left)
        self.right = ItemSet(right)
        self.union = ItemSet(self.right.union(self.left))
        self.confidence = None
        self.support = None

    def __repr__(self):
        left = [str(x) for x in sorted(self.left)]
        right = [str(x) for x in sorted(self.right)]
        return "%s,%s,%f,%f" % (" ".join(left), " ".join(right), self.support, self.confidence)

    def tostring(self, goods):
        return "%s\n  %s\n    %f,%f" % (
            self.left.tostring(goods,stats=False),
            self.right.tostring(goods,stats=False),
            self.support, self.confidence)


class Dataset:
    def __init__(self, entries, minSup=0.0):
        if minSup < 0 or minSup >= 1:
            raise ValueError("Minimum support must be in [0.0, 1.0)")
        self.numEntries = len(entries)
        self.minSup=minSup

        # Strip first item and turn entries into sets.
        # Determine the number of items.
        # Establish baseline counts.
        self.entries = []
        self.numItems = 0
        self.counts = dict()
        for entry in entries:
            converted = set(int(i) for i in entry[1:])
            self.entries.append(converted)
            self.numItems = max(self.numItems, max(converted))
            for i in converted:
                try: self.counts[i] += 1
                except KeyError: self.counts[i] = 1

        # Add one since items are listed by indices.
        self.numItems += 1

        # Initialize itemsets dictionary.
        # Add single-item itemsets.
        self.itemsets = dict()
        self.addItemsets([ItemSet((i,)) for i in xrange(self.numItems)])

    def apriori(self, skyline=False, verbose=False):
        # Generate candidates of increasing size until none are found.
        # Sets of size 1 already exist in the dataset.
        previousSet = self.getItemsets(1)
        k = 2
        while len(previousSet) > 0:
            candidates = candidateGen(previousSet, k)
            # Add candidates.  Ones that do not meet the minimum support will
            # not be added.  The collection of added itemSets is returned.
            previousSet = self.addItemsets(candidates)
            if verbose: print("%d: %d" % (k, len(previousSet)))
            k += 1
        return sorted(self.getItemsets(skyline=skyline), key=lambda x:x.support, reverse=True)

    def genRules(self, minConf=0.0, skyline=False, verbose=False):
        # Ensure apriori has been run.
        if 2 not in self.itemsets:
            itemsets = self.apriori(skyline, verbose)
        else:
            itemsets = self.getItemsets(skyline=skyline)
        itemsets = [s for s in itemsets if len(s) > 1]

        rules = []
        sets = []

        for itemset in itemsets:
            for item in itemset:
                r = AssociationRule(itemset.difference([item]), [item])
                rules.append(r)
                sets.append(r.left)
                sets.append(r.right)
                sets.append(r.union)

        self.getSupport(sets)
        filtered = []

        for r in rules:
            r.confidence = r.union.support / r.left.support
            r.support = r.union.support
            if r.confidence > minConf:
                filtered.append(r)
        return sorted(filtered, key=lambda x:x.confidence, reverse=True)

    def getSupport(self, itemsets):
        """
        Calculates the support for a given set item sets.
        Indices should not be negative or exceed the greatest index.
        """
        # Calculate the number of entries containing the given indices
        # in the itemset.
        for itemset in itemsets:
            itemset.support = 0

        for entry in self.entries:
            for itemset in itemsets:
                if itemset.items.issubset(entry): itemset.support += 1

        for itemset in itemsets:
            itemset.support = float(itemset.support) / self.numEntries

    def addItemsets(self, itemsets):
        """
        Adds item sets if its support exceeds the dataset's minSup.
        """
        added = []
        self.getSupport(itemsets)

        for itemSet in itemsets:
            if itemSet.support > self.minSup:
                l = self.itemsets.setdefault(len(itemSet), [])
                if itemSet not in l:
                    l.append(itemSet)
                    added.append(itemSet)
        return added

    def getItemsets(self, skyline=False, length=None):
        """
        Gets a list of item sets.
        If |length| is provided, only sets of the given length are returned.
        If |skyline|, only skyline itemsets are returned.  Skyline itemsets are
            those that are not a subset of any other itemset.
        """
        if length: items = self.itemsets.get(length, [])
        else: items = [x for sublist in self.itemsets.values() for x in sublist]

        if skyline:
            # Return only sets that are not a subset of any other set.
            return [item for item in items
                    if not any(item != other and item.issubset(other)
                               for other in items)]
        else: return items

