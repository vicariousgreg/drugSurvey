#!/usr/bin/python2
#
# Authors:      Greg Davis
#               Daniel Kauffman
# Assignment:   Lab 5
# Course:       CPE 466
# Instructor:   A. Dekhtyar
# Term:         Fall 2015

from __future__ import print_function
import argparse
import csv
import math
import random
import sys


def main():
    args = set_options()
    if args.verbose:
        print("Options:", str(vars(args)))
    
    with open(args.goods, "r") as goodsfile:
        goods = [line.strip() for line in goodsfile.readlines() if len(line) > 0]

    with open(args.csvfile, "r") as csvfile:
        lines = [line for line in csv.reader(csvfile) if len(line) > 0]
        #restrictions = lines[0]
        #points = [Point(line, restrictions) for line in lines[1:]]
        points = [Point(line) for line in lines]

    clusters = kmeans(points, args.k)
    for index,cluster in enumerate(clusters):
        print("==============================================")
        print("Cluster %2d (%3d points, SSE: %7.3f):" % (index, len(cluster.points), cluster.get_SSE()))
        subsets = [[] for _ in xrange(3)]
        for point in cluster.points:
            substances = []
            for i,x in enumerate(point.coordinates):
                if x > 0:
                    substances.append(goods[i])
                    #subsets[int(x**0.5)-1].append(goods[i])
                    subsets[int(x)-1].append(goods[i])
            #print(", ".join(substances))
            #print("  " + str(point))
        categories = ["Once", "Month", "Daily"]
        for i, subset in enumerate(subsets):
            out = []
            for substance in sorted(set(subset), reverse=True, key = lambda x: subset.count(x)):
                #if len(cluster.points) == 1 or subset.count(substance) > 1:
                if True:
                    out.append("  %30s  %3d  %6.2f" % (substance,
                        subset.count(substance),
                        100.0*float(subset.count(substance))/len(cluster.points)))
            if len(out) > 0:
                print(" ", categories[i])
                for line in out: print(line)
                print("")
        print("")


def set_options():
    """
    Retrieve the user-entered arguments for the program.
    """
    parser = argparse.ArgumentParser(description = 
    """Perform k-means clustering on a given data set.""")
    parser.add_argument("csvfile", help = 
    """the comma-separated values file with data on which to perform 
       clustering""")
    parser.add_argument("goods", help = 
    """the goods file""")
    parser.add_argument("k", type = int, help = 
    """the number of clusters to create""")
    parser.add_argument("-v", "--verbose", action = "store_true", help = 
    """print additional information to the terminal as the program is 
       executing""")
    return parser.parse_args()

def calculateAverage(entries):
    return [sum(entry[i] for entry in entries) / len(entries) for i in xrange(len(entries[0]))]
 
def selectInitialCentroids(dataset, k):
    # Get a subset of the data of size k * 5
    size = max(min(len(dataset) / 2, k * 5), k)
    copy = [d for d in dataset]
    random.shuffle(copy)

    super_centroid = Point(calculateAverage(dataset))

    dataset = set(copy[:size])
    m1 = max((d for d in dataset), key=lambda x: x.get_distance(super_centroid))
    dataset.remove(m1)
    m2 = max((d for d in dataset), key=lambda x: x.get_distance(m1))
    dataset.remove(m2)
    centroids = [m1, m2]

    for _ in xrange(k - 2):
        mi = max((d for d in dataset), key=lambda x: sum(x.get_distance(m) for m in centroids))
        centroids.append(mi)
        dataset.remove(mi)

    return centroids

def stoppingCondition(old_SSE, SSE):
    threshold = 0.00001
    diff = old_SSE - SSE
    return diff < threshold

def kmeans(dataset, k):
    centroids = selectInitialCentroids(dataset, k)
    old_SSE = sys.maxint
    done = False

    while not done:
        clusters = []
        for _ in xrange(k):
            clusters.append([])
        for d in dataset:
            index = min((i for i in xrange(k)), key = lambda x:d.get_distance(centroids[x]))
            clusters[index].append(d)
        centroids = []
        for entries in clusters:
            try: centroids.append(Point(calculateAverage(entries)))
            except IndexError: centroids.append(dataset[random.randint(0, len(dataset)-1)])
        #centroids = [Point(calculateAverage(entries)) for entries in clusters]
        SSE = sum(Cluster(centroid,cluster).get_SSE() for centroid,cluster in zip(centroids, clusters))
        done = stoppingCondition(old_SSE, SSE)
        old_SSE = SSE
    return [Cluster(centroid, points) for centroid,points in zip(centroids, clusters)]

class Cluster:
    
    def __init__(self, centroid, points):
        self.points = points
        self.centroid = centroid

    def get_max_distance(self):
        try: return max(d.get_distance(self.centroid) for d in self.points)
        except ValueError: return 0.0

    def get_min_distance(self):
        try: return min(d.get_distance(self.centroid) for d in self.points)
        except ValueError: return 0.0

    def get_average_distance(self):
        try: return sum(d.get_distance(self.centroid) for d in self.points) / len(self.points)
        except ValueError: return 0.0

    def get_SSE(self):
        try: return sum(d.get_distance(self.centroid) ** 2 for d in self.points)
        except ValueError: return 0.0

class Point:
    
    def __init__(self, coordinates, restrictions=None):
        self.data = coordinates
        if restrictions is not None:
            self.coordinates = []
            for i,v in enumerate(restrictions):
                if v == "1": self.coordinates.append(float(coordinates[i]))
        else:
            self.coordinates = [float(x) for x in coordinates]
    
    def __str__(self):
        return "(" + ", ".join([str(c) for c in self.data]) + ")"

    def __str__(self):
        return ", ".join([str(d) for d in self.data])
    
    def __repr__(self):
        return str(self)

    def __len__(self):
        return len(self.coordinates)

    def __getitem__(self, index):
        return self.coordinates[index]
    
    def get_distance(self, other):
        """
        Return the Euclidean distance between this point and |other|.
        """
        if len(self.coordinates) != len(other.coordinates):
            raise ValueError
        return math.sqrt(sum([(self.coordinates[i] - other.coordinates[i]) ** 2 
                              for i in range(len(self.coordinates))]))


if __name__ == "__main__":
    main()


