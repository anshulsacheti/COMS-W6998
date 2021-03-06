#!/usr/local/bin/python3
import argparse
import networkx as nx
import pdb
import time
import numpy as np
import pandas as pd
import datetime
import random

# Read in graph
def generateInstagramGraph():
    """
    Generate edge graph via networkx and edge file

    Input:
        None

    Output:
        Networkx graph with edges + node genders

    Returns
        G: nx edge graph
    """

    G = nx.read_edgelist(path="graph_edges.csv", nodetype=int, delimiter=',')

    with open("graph_gender.csv", "r") as file:
        for i,line in enumerate(file.readlines()):
            data = line.split("\n")
            node, gender = data[0].split(",")
            G.add_node(int(node))
            nx.set_node_attributes(G, name="gender", values={int(node):gender})

    return G

# Read in graph
def generateStackOverflowGraph():
    """
    Generate edge graph via networkx and edge file

    Input:
        None

    Output:
        Networkx graph with edges + node genders

    Returns
        G: nx edge graph
    """

    G = nx.read_edgelist(path="nodeTimestampEdges_subset.csv", nodetype=int, delimiter=',')

    with open("nodeTimestampCategory.csv", "r") as file:
        for i,line in enumerate(file.readlines()):
            data = line.split("\n")
            node, relativeTimestamp = data[0].split(",")
            G.add_node(int(node))
            nx.set_node_attributes(G, name="relativeTimestamp", values={int(node):relativeTimestamp})

    return G

def runCustomAlgo(G, predictNodes, dataset):
    """
    Run Custom algorithm and generate edge recommendations for nodes in file

    Input:
        G - networkx graph
        predictNodes - list of nodes to predict
        dataset - string indicating what dataset is being run

    Output:
        nodeRecPair - dict of node recommendations
        scoreDict - dict of node rec scores

    Returns:
        list of dicts, [nodeRecPair, scoreDict]
    """

    graphNodes = list(G.nodes)

    neighborsDict = {}
    scoreDict = {}
    predictions = []

    nodeRecPair = dict(zip(predictNodes, [0]*len(predictNodes)))

    # Run custom algo on all nodes
    nodesCompleted = 0
    for i,node1 in enumerate(nodeRecPair):

        # Untouched nodes
        if nodeRecPair[node1]==0:

            #Only nodes within a distance 2 of base node can have neighbors
            possibleNeighbors = list(nx.ego_graph(G,node1,radius=2).nodes())
            possibleNeighborSet = set(possibleNeighbors)

            node1_neighbors = list(G.neighbors(node1))
            neighborsDict[node1] = node1_neighbors
            scoreDict[node1] = {}

            if nodesCompleted % 2000 == 0:
                print("Finished %d nodes, %s" % (nodesCompleted, datetime.datetime.time(datetime.datetime.now())))
            nodesCompleted += 1

            # Calculate score per node
            for node2 in possibleNeighbors:

                # Ego graph returns list of nodes including input node and it's neighbors
                if node2 == node1 or node2 in node1_neighbors:
                    continue
                else:
                    if node2 in neighborsDict:
                        node2_neighbors = neighborsDict[node2]
                    else:
                        node2_neighbors = list(G.neighbors(node2))
                        neighborsDict[node2] = node2_neighbors

                node1_neighbors = set(node1_neighbors)
                node2_neighbors = set(node2_neighbors)
                intersect = node1_neighbors.intersection(node2_neighbors)

                # Calculate score
                if intersect:
                    score = 0
                    # Update score against all neighbors
                    for n1 in intersect:
                        if n1 in neighborsDict:
                            neighbors = neighborsDict[n1]
                        else:
                            neighbors = list(G.neighbors(n1))
                            neighborsDict[n1] = neighbors
                        total = 0
                        for n2 in neighbors:
                            if n2 in possibleNeighborSet:
                                total += 1
                        if total>1:
                            score += 1/np.log(total)
                    scoreDict[node1][node2] = score

            # Choose best score for edge recommendation
            # Add new node/edge to graph with props
            try:
                bestNode = max(scoreDict[node1], key=scoreDict[node1].get)
            except ValueError:
                bestNode = np.random.choice(graphNodes)
                while bestNode==node1 or bestNode in node1_neighbors:
                    bestNode = np.random.choice(graphNodes)
            nodeRecPair[node1] = (node1, bestNode)

            # Testing
            if 0==1 and len(scoreDict[node1].keys())<6 and len(node1_neighbors)<6:
                print("Base Node: %d, NodeRec: %d" % (node1, bestNode))
                print("ScoreDict: %s" % scoreDict[node1])
                print("Neighbors: %s" % node1_neighbors)
                print("-----------\n")
            # predictions.extend([(node1, bestNode)])

    # Write all recommendations out
    with open("predicted_nodes_custom_"+dataset+".csv", "w") as predicted:
        for p in predictNodes:
            predicted.write("{}\n".format(nodeRecPair[p]))

    return [nodeRecPair, scoreDict]


def runAdamicAdar(G, predictNodes, dataset):
    """
    Run Adamic adar algorithm and generate edge recommendations for nodes in file

    Input:
        G - networkx graph
        predictNodes - list of nodes to predict
        dataset - string indicating what dataset is being run

    Output:
        nodeRecPair - dict of node recommendations
        scoreDict - dict of node rec scores

    Returns:
        list of dicts, [nodeRecPair, scoreDict]
    """

    graphNodes = list(G.nodes)

    neighborsDict = {}
    scoreDict = {}
    predictions = []

    nodeRecPair = dict(zip(predictNodes, [0]*len(predictNodes)))

    # Run adamic adar on all nodes
    nodesCompleted = 0
    for i,node1 in enumerate(nodeRecPair):

        # Untouched nodes
        if nodeRecPair[node1]==0:

            #Only nodes within a distance 2 of base node can have neighbors
            possibleNeighbors = list(nx.ego_graph(G,node1,radius=2).nodes())

            node1_neighbors = list(G.neighbors(node1))
            neighborsDict[node1] = node1_neighbors
            scoreDict[node1] = {}

            if nodesCompleted % 2000 == 0:
                print("Finished %d nodes, %s" % (nodesCompleted, datetime.datetime.time(datetime.datetime.now())))
            nodesCompleted += 1

            # Calculate score per node
            for node2 in possibleNeighbors:

                # Ego graph returns list of nodes including input node and it's neighbors
                if node2 == node1 or node2 in node1_neighbors:
                    continue
                else:
                    if node2 in neighborsDict:
                        node2_neighbors = neighborsDict[node2]
                    else:
                        node2_neighbors = list(G.neighbors(node2))
                        neighborsDict[node2] = node2_neighbors

                intersect = set(node1_neighbors).intersection(set(node2_neighbors))

                # Calculate score
                if intersect:
                    score = 0
                    # Update score against all neighbors
                    for n in intersect:
                        if n in neighborsDict:
                            neighbors = neighborsDict[n]
                        else:
                            neighbors = list(G.neighbors(n))
                            neighborsDict[n] = neighbors
                        score += 1/np.log(len(neighbors))
                    scoreDict[node1][node2] = score

            # Choose best score for edge recommendation
            # Add new node/edge to graph with props
            try:
                bestNode = max(scoreDict[node1], key=scoreDict[node1].get)
            except ValueError:
                bestNode = np.random.choice(graphNodes)
                while bestNode==node1 or bestNode in node1_neighbors:
                    bestNode = np.random.choice(graphNodes)
            nodeRecPair[node1] = (node1, bestNode)

            # Testing
            if 0==1 and len(scoreDict[node1].keys())<6 and len(node1_neighbors)<6:
                print("Base Node: %d, NodeRec: %d" % (node1, bestNode))
                print("ScoreDict: %s" % scoreDict[node1])
                print("Neighbors: %s" % node1_neighbors)
                print("-----------\n")
            # predictions.extend([(node1, bestNode)])

    # Write all recommendations out
    with open("predicted_nodes_aa_"+dataset+".csv", "w") as predicted:
        for p in predictNodes:
            predicted.write("{}\n".format(nodeRecPair[p]))

    return [nodeRecPair, scoreDict]

def calculateFairness(G, nodeRecPair, dataset):
    """
    Calculate Graph G fairness against Graph with adamicAdar run to generate new edges

    Input:
        G - networkx graph
        nodeRecPair - dict of nodes and their recommended new edge
        dataset - string indicating what dataset is being run

    Output:
        Fairness score

    Returns:
        float
    """
    G_degrees = sorted(G.degree, key=lambda x: x[1], reverse=True)

    # Count number of recommendations for a given node
    # Sort nodes vy number of recs
    G_aa = {}
    for key in nodeRecPair:
        _, recNode = nodeRecPair[key]
        if recNode in G_aa:
            G_aa[recNode] += 1
        else:
            G_aa[recNode] = 1
    G_aa_degrees = sorted(G_aa, key = G_aa.get, reverse=True)
    # G_aa_degrees = sorted(G_aa.degree, key=lambda x: x[1], reverse=True)

    # Set up dataset specific vars
    if dataset=='IG':
        attr = 'gender'
        attrVal = 'F'
    else:
        attr ='relativeTimestamp'
        attrVal = 'B'

    # Calculate fairness score
    # Calculate number of nodes that meet percentage criteria and find % of females
    fairnessScore = 0.0
    for percent in [0.01, 0.10, 0.25]:

        numOrig = int(len(G_degrees)*percent)
        numRec  = int(len(G_aa_degrees)*percent)

        G_subset    = [node for node, degree in G_degrees[0:numOrig]]
        G_aa_subset = G_aa_degrees[0:numRec]

        G_femaleCount    = sum([G.node[node][attr]==attrVal for node in G_subset])/numOrig
        G_aa_femaleCount = sum([G.node[node][attr]==attrVal for node in G_aa_subset])/numRec

        fairnessScore += abs(G_femaleCount-G_aa_femaleCount)

    print("Final fairness score: %f" % fairnessScore)
    return fairnessScore

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--customAlgo", action="store_true")
    parser.add_argument("--SO", action="store_true")
    parser.add_argument("--iters", type=int)

    args = parser.parse_args()

    totalFairnessCount = 0
    totalPercentCorrect = 0

    for i in range(args.iters):
        if args.SO:
            G = generateStackOverflowGraph()
            dataset = 'SO'
        else:
            G = generateInstagramGraph()
            dataset = 'IG'

        if args.test:
            # Remove set of edges and test if they are added back in
            edgeList = list(G.edges())
            edgesRemoved = {}
            removedEdgeList = []
            predictNodes = []
            # Num of edges to make SO and IG comparable in number of edges
            for i in range(100000):
                edge = random.choice(edgeList)
                try:
                    G.remove_edge(*edge)
                except nx.exception.NetworkXError:
                    continue
                removedEdgeList.extend([edge])
                predictNodes.extend([edge[0]])

            # Write all nodes to recommend out
            if dataset=='SO':
                with open("nodes_predict_"+dataset+".csv", "w") as to_predict:
                    for p in predictNodes:
                        to_predict.write("{}\n".format(p))
        else:
            # Read in all nodes to predict
            with open("nodes_predict.csv") as nodes:
                nodes_predict = nodes.read().splitlines()
            predictNodes = [int(node) for node in nodes_predict]

        if args.customAlgo:
            nodeRecPair, scoreDict = runCustomAlgo(G, predictNodes, dataset)
        else:
            nodeRecPair, scoreDict = runAdamicAdar(G, predictNodes, dataset)


        if args.test:
            matchCount = 0.0
            generalMatchCount = 0.0
            valMatchCount = 0.0
            sharedNeighborCount = 0.0
            for source, dest in removedEdgeList:
                if dest == nodeRecPair[source][1]:
                    matchCount += 1.0

                if dest in scoreDict[source]:
                    generalMatchCount += 1.0
                    if scoreDict[source][nodeRecPair[source][1]] == scoreDict[source][dest]:
                        valMatchCount += 1.0

                source_neighbors = list(G.neighbors(source))
                dest_neighbors = list(G.neighbors(dest))
                intersect = set(source_neighbors).intersection(set(dest_neighbors))
                if intersect:
                    sharedNeighborCount += 1.0

            print("Percent correct: %f" % (matchCount/len(removedEdgeList)))
            print("Percent in neighbor set: %f" % (generalMatchCount/len(removedEdgeList)))
            print("Percent same value: %f" % (valMatchCount/generalMatchCount if valMatchCount>0 else 0))
            print("Percent shared neighbor count: %f" % (sharedNeighborCount/len(removedEdgeList)))
            totalPercentCorrect += matchCount/len(removedEdgeList)
        fairnessVal = calculateFairness(G, nodeRecPair, dataset)
        totalFairnessCount += fairnessVal

        print("---------------------------")

    print("Average Fairness: %f" % (totalFairnessCount/args.iters))
    print("Average Percent correct: %f" % (totalPercentCorrect/args.iters))
