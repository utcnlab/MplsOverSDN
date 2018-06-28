import argparse
import json
from mininet.cli import CLI
from mininet.log import lg
from mininet.node import RemoteController, OVSSwitch
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from functools import partial
from networkx.readwrite import json_graph

OVSSwitch13 = partial(OVSSwitch, protocols='OpenFlow13')


def bytes_to_int(bytes):
    return int(bytes.encode('hex'), 16)


def hex_strip(n):
    hexString = hex(n)
    plainString = hexString.split("0x")[1]  # Gets rid of the Ox of the hex string
    return plainString.split("L")[0]  # Gets rid of the trailing L if any


class GraphTopoFixedAddrPorts(Topo):
    def __init__(self, graph, **opts):
        listenPort = 6634
        Topo.__init__(self, **opts)
        nodes = graph.nodes()
        node_names = {}
        for node in nodes:  # node is the unicode string name of the node
            tmp_node = graph.node[node]
            if tmp_node['type'] == 'switch':
                our_dpid = hex_strip(bytes_to_int(node.encode('ascii')))
                print "Node: {} dpid: {}".format(node, our_dpid)
                switch = self.addSwitch(node.encode('ascii'), listenPort=listenPort,
                                        dpid=our_dpid)
                listenPort += 1
                node_names[node.encode('ascii')] = switch
            else:
                host = self.addHost(node.encode('ascii'), **tmp_node)
                node_names[node.encode('ascii')] = host
        edges = graph.edges()
        for edge in edges:
            props = graph.get_edge_data(edge[0], edge[1])
            delay = str(props['weight']) + "ms"
            bw = props['capacity']
            port1 = props['ports'][edge[0]]
            port2 = props['ports'][edge[1]]
            self.addLink(node_names[edge[0]], node_names[edge[1]], port1=port1, port2=port2,
                         delay=delay, bw=bw)

    @staticmethod
    def from_file(filename):
        f = open(filename)
        tmp_graph = json_graph.node_link_graph(json.load(f))
        f.close()
        return GraphTopoFixedAddrPorts(tmp_graph)


if __name__ == '__main__':
    fname = "./topologies/simpleNet.json"  # You can put your default file here
    remoteIP = "127.0.0.1"  # Put your default remote IP here
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--fname", help="network graph file name")
    parser.add_argument("-ip", "--remote_ip", help="IP address of remote controller")
    args = parser.parse_args()
    if not args.fname:
        print "fname not specified using: {}".format(fname)
    else:
        fname = args.fname
    if not args.remote_ip:
        print "remote controller IP not specified using: {}".format(remoteIP)
    else:
        remoteIP = args.remote_ip
    topo = GraphTopoFixedAddrPorts.from_file(fname)
    lg.setLogLevel('info')
    network = Mininet(controller=RemoteController, autoStaticArp=True, link=TCLink, switch=OVSSwitch13)
    network.addController(controller=RemoteController, ip=remoteIP)
    network.buildFromTopo(topo=topo)
    network.start()
    CLI(network)
    network.stop()
