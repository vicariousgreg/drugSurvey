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
import copy
import csv
import math
import os
import sys

from xml.etree import cElementTree as et


def main():
    args = set_options()
    if args.verbose:
        print("Options:", str(vars(args)))
    
    labeled = ["iris"]
    with open(args.csv, "r") as csv_file:
        lines = [line for line in csv.reader(csv_file) if len(line) > 0]
        restricted = [i for i in range(len(lines[0])) if lines[0][i] != "0"]
        clusters = []
        for line in lines[1:]:
            filtered = [line[i] for i in restricted]
            label = line[-1] if get_root_name(args.csv) in labeled else None
            clusters.append(Cluster(Point(filtered, label)))
    
    cut_clusters = []
    while len(clusters) > 1:
        closest_distance = sys.maxint
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                distance = clusters[i].get_distance(clusters[j], args.method)
                if distance < closest_distance:
                    closest_clusters = [clusters[i], clusters[j]]
                    closest_distance = distance
        if ((len(cut_clusters) == 0 and closest_distance > args.threshold) or
                len(clusters) == args.num_clusters):
            cut_clusters = copy.deepcopy(clusters)
        c1, c2 = closest_clusters
        clusters.append(Cluster([c1, c2], closest_distance))
        clusters.remove(closest_clusters[0])
        clusters.remove(closest_clusters[1])
    if args.threshold < sys.maxint and len(cut_clusters) == 0:
        cut_clusters = clusters
    dendrogram = create_xml(get_root_name(args.csv) + ".xml", clusters[0])
    et.ElementTree(dendrogram).write(sys.stdout)
    print_cluster_data(cut_clusters)


def set_options():
    """
    Retrieve the user-entered arguments for the program.
    """
    parser = argparse.ArgumentParser(description = 
    """Perform hierarchical clustering on a given data set.""")
    parser.add_argument("csv", metavar = "CSV FILE", help = 
    """the comma-separated values (CSV) file with data on which to perform 
       hierarchical clustering""")
    parser.add_argument("-m", "--method", default = "average", 
                        choices = ["single", "complete", "average", 
                                   "centroid", "ward"], help = 
    """the method to use for finding the distance between clusters""")
    parser.add_argument("-n", "--num-clusters", type = int, default = 1, help = 
    """the number of clusters at which to stop merging given a sufficiently 
       high threshold""")
    parser.add_argument("-t", "--threshold", type = float, 
                        default = float(sys.maxint), help = 
    """the maximum distance at which to merge clusters""")
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


def create_xml(xml_path, cluster, write = False):
    c1, c2 = cluster.hierarchy
    tree = et.Element("tree", height = str(cluster.height))
    add_xml_node(tree, c1)
    add_xml_node(tree, c2)
    indent(tree)
    if write:
        f = open(xml_path, "w")
        f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
        et.ElementTree(tree).write(f)
        f.close()
    return tree


def add_xml_node(parent, child):
    c1 = child.hierarchy[0]
    if isinstance(c1, Point):
        et.SubElement(parent, "leaf", height = "0.0", data = str(c1))
    else:
        c2 = child.hierarchy[1]
        node = et.SubElement(parent, "node", height = str(child.height))
        add_xml_node(node, c1)
        add_xml_node(node, c2)


def indent(elem, level = 0, length = 2):
    """
    XML pretty-printing function from:
        http://effbot.org/zone/element-lib.htm#prettyprint
    """
    i = "\n" + level * (" " * length)
    if len(elem) > 0:
        if not elem.text or not elem.text.strip():
            elem.text = i + (" " * length)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def print_cluster_data(clusters):
    """
    Print the cluster centroid, the minimum, maximum, and average distances
    from the cluster's points to the centroid, and the data for each point
    in the cluster for each cluster in |clusters|.
    """
    for i, c in enumerate(clusters):
        print("\nCluster {0:d}:".format(i))
        print((" " * 1) + "Height: {0}".format(c.height))
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
    
    def __init__(self, clusters, height = 0.0):
        """
        Initialize a cluster with either a point or a list of two clusters,
        passed in as |clusters|. In the latter case, set the height of this
        cluster to be |height|, the distance between the two argument clusters.
        """
        if isinstance(clusters, Point):
            point = clusters
            self.points = (point,)
            self.hierarchy = (point,)
            self.centroid = point
        else:
            c1, c2 = clusters
            if not isinstance(c1, Cluster) or not isinstance(c2, Cluster):
                raise ValueError("Invalid Cluster Constructor Argument")
            self.points = c1.points + c2.points
            self.hierarchy = (c1, c2)
            self.centroid = self.get_centroid()
        self.height = round(height, 1)
        self.ctr_dists = None
        self.sse = None
    
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
    
    def get_distance(self, other, method = "average"):
        """
        Return the distance between this cluster and |other|.
        """
        if method == "centroid":
            return self.centroid.get_distance(other.centroid)
        elif method == "ward":
            if self.sse is None:
                self.get_sse()
            if other.sse is None:
                other.get_sse()
            merged = Cluster([self, other])
            merged.get_sse()
            return merged.sse - (self.sse + other.sse)
        else:
            distances = []
            for sp in self.points:
                for op in other.points:
                    distances.append(sp.get_distance(op))
            if method == "single":
                return reduce(min, distances)
            elif method == "complete":
                return reduce(max, distances)
            elif method == "average":
                return sum(distances) / float(len(distances))
            else:
                raise ValueError("Invalid Distance Method")




class Point():
    
    def __init__(self, data, label = None):
        self.data = [float(d) for d in data]
        self.label = label
    
    def __str__(self):
        appended = "" if self.label is None else " ({0})".format(self.label)
        return ", ".join([str(d) for d in self.data]) + appended
    
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


if __name__ == "__main__":
    main()


