#!/usr/bin/env python

import pylab as p
import networkx as nx
from networkx.readwrite import json_graph
import json
import sys


def save(G, fname):
    with open(fname, 'w') as fd:
        fd.write(json.dumps(json_graph.node_link_data(G)))


def read_json_file(filename):
    with open(filename) as f:
        js_graph = json.load(f)
    return json_graph.node_link_graph(js_graph)


nx.draw(read_json_file('simpleNet.json' if len(sys.argv) < 2 else sys.argv[1]), with_labels=True)
p.show()
