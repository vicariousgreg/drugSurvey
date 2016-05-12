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
import os


def main():
    args = set_options()
    if args.verbose:
        print("Options:", str(vars(args)))
    
    labeled = ["iris", "iris-abbr"]
    with open(args.csv, "r") as csv_file:
        lines = [line for line in csv.reader(csv_file) if len(line) > 0]
        restricted = [i for i in range(len(lines[0])) if lines[0][i] != "0"]
        points = []
        for line in lines[1:]:
            filtered = [line[i] for i in restricted]
            label = line[-1] if get_root_name(args.csv) in labeled else None
            points.append(Point(filtered, label))
    
    for p in points:
        p.set_neighborhood(points, args.epsilon)
        if len(p.neighborhood) >= args.min_points:
            p.set_type("CORE")
    for p in points:
        if p.pt_type is None:
            core_pts = filter(lambda x : x.pt_type == "CORE", p.neighborhood)
            pt_type = "BOUNDARY" if len(core_pts) > 0 else "NOISE"
            p.set_type(pt_type)
    
    clusters = []
    core_pts = filter(lambda x : x.pt_type == "CORE", points)
    for p in core_pts:
        if p.cluster is None:
            clusters.append(Cluster(p))
            find_density_connected(p, clusters[-1])
    print_cluster_data(clusters)
    print("\nNoise:")
    noise_pts = filter(lambda x : x.pt_type == "NOISE", points)
    fmt_str = "{0:d} Point:" if len(noise_pts) == 1 else "{0:d} Points:"
    print((" " * 1) + fmt_str.format(len(noise_pts)))
    for p in noise_pts:
        print((" " * 2) + str(p))



def set_options():
    """
    Retrieve the user-entered arguments for the program.
    """
    parser = argparse.ArgumentParser(description = 
    """Perform DBSCAN clustering on a given data set.""")
    parser.add_argument("csv", metavar = "CSV FILE", help = 
    """the comma-separated values (CSV) file with data on which to perform 
       DBSCAN clustering""")
    parser.add_argument("-m", "--min-points", metavar = "MIN POINTS", 
                        type = int, default = 40, help = 
    """the minimum number of points required in a point's neighborhood for it
       to be a core point""")
    parser.add_argument("-e", "--epsilon", metavar = "MAX DISTANCE", 
                        type = float, default = 0.9, help = 
    """the maximum distance between two points necessary for neighborhood 
       membership""")
    parser.add_argument("-v", "--verbose", action = "store_true", help = 
    """print additional information to the terminal as the program is 
       executing""")
    return parser.parse_args()


def get_root_name(path):
    """
    Return the root name of |path| by cutting out extensions and any
    higher-level directories that may be in the path.
    """
    return os.path.splitext(os.path.basename(path))[0]


def find_density_connected(core_pt, cluster):
    """
    Recursively search for points that are density-connected to |core_pt| and 
    add them to |cluster|.
    """
    for p in core_pt.neighborhood:
        cluster.add_point(p)
        if p.pt_type == "CORE" and p.cluster is None:
            find_density_connected(p, cluster)


def print_cluster_data(clusters):
    """
    Print the cluster centroid, the minimum, maximum, and average distances
    from the cluster's points to the centroid, and the data for each point
    in the cluster for each cluster in |clusters|.
    """
    for i, c in enumerate(clusters):
        print("\nCluster {0:d}:".format(i))
        print((" " * 1) + "Center: {0}".format(c.centroid))
        if c.sse is None:
            c.get_sse()
        max_dist = round(reduce(max, c.ctr_dists), 2)
        min_dist = round(reduce(min, c.ctr_dists), 2)
        avg_dist = round(sum(c.ctr_dists) / float(len(c.ctr_dists)), 2)
        print((" " * 2) + "Max Dist to Center: " + str(max_dist))
        print((" " * 2) + "Min Dist to Center: " + str(min_dist))
        print((" " * 2) + "Avg Dist to Center: " + str(avg_dist))
        print((" " * 2) + "SSE: " + str(c.sse))
        fmt_str = "{0:d} Point:" if len(c.points) == 1 else "{0:d} Points:"
        print((" " * 1) + fmt_str.format(len(c.points)))
        for p in c.points:
            print((" " * 2) + str(p))




class Cluster():
    
    def __init__(self, point):
        point.cluster = self
        self.points = [point]
        self.centroid = point
        self.ctr_dists = None
        self.sse = None
    
    def add_point(self, point):
        """
        Add |point| to this cluster and update its centroid."
        """
        point.cluster = self
        self.points += [point]
        self.centroid = self.get_centroid()
    
    def get_centroid(self):
        """
        Calculate the centroid of this cluster.
        """
        all_data = [p.data for p in self.points]
        transposed = zip(*all_data)
        mid_data = [round(sum(d) / float(len(d)), 1) for d in transposed]
        return Point(mid_data)
    
    def get_sse(self):
        """
        Calculate the Sum of Squared Errors between all points in this cluster
        and its centroid.
        """
        self.ctr_dists = [p.get_distance(self.centroid) for p in self.points]
        self.sse = round(sum([d ** 2 for d in self.ctr_dists]), 2)




class Point():
    
    def __init__(self, data, label = None):
        self.data = [float(d) for d in data]
        self.label = label
        self.neighborhood = None
        self.pt_type = None
        self.cluster = None
    
    def __str__(self):
        pt = "" if self.pt_type is None else " [{0}]".format(self.pt_type[0]) 
        appended = "" if self.label is None else " ({0})".format(self.label)
        return ", ".join([str(d) for d in self.data]) + pt + appended
    
    def __repr__(self):
        return str(self)
    
    def get_distance(self, other):
        """
        Return the Euclidean distance between this point and |other|.
        """
        if len(self.data) != len(other.data):
            raise ValueError
        return math.sqrt(sum([(self.data[i] - other.data[i]) ** 2 
                              for i in range(len(self.data))]))
    
    def set_neighborhood(self, points, epsilon):
        """
        Set this point's neighborhood to be a list of all points within 
        |epsilon| distance to this point.
        """
        self.neighborhood = [p for p in points if p is not self and 
                                               self.get_distance(p) <= epsilon]
    
    def set_type(self, pt_type):
        """
        Set the type of this point to |pt_type|.
        """
        if pt_type not in ["CORE", "BOUNDARY", "NOISE"]:
            raise ValueError("Invalid Point Type")
        self.pt_type = pt_type


if __name__ == "__main__":
    main()


