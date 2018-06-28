import random
from collections import defaultdict, OrderedDict
import json
from networkx.readwrite import json_graph
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.cmd import manager  # For directly starting Ryu
import sys  # For getting command line arguments and passing to Ryu
import eventlet
from eventlet import backdoor  # For telnet python access
from ryu.ofproto import ofproto_v1_3  # This code is OpenFlow 1.0 specific
from ryu.lib.packet.packet import Packet  # For packet parsing
import ryu.lib.packet.ipv4
import ryu.lib.packet.mpls
from ryu.controller.handler import set_ev_cls
import networkx as nx

if __name__ == "__main__":  # Stuff to set additional command line options
    from ryu import cfg

    CONF = cfg.CONF
    CONF.register_cli_opts([
        cfg.StrOpt('netfile', default=None, help='network json file'),
        cfg.BoolOpt('notelnet', default=False,
                    help='Telnet based debugger.')
    ])


def convert_array_to_path_string(arr):
    string = ""
    for i in range(len(arr)):
        if i == 0:
            string += arr[i]
        elif i == len(arr):
            string += arr[i]
        else:
            string += "-{}".format(arr[i])
    return string


def get_all_graph_link_labels(g):
    nodes = g.nodes()
    link_labels = {}
    for n1 in nodes:
        for n2 in nodes:
            if n1 == n2:
                continue
            link_labels[(str(n1), str(n2))] = (str(n1), str(n2))
    return link_labels


def get_all_graph_paths(g, only_hosts=True):
    nodes = g.nodes()
    shortest_paths = []
    for n1 in nodes:
        for n2 in nodes:
            if only_hosts and (n1[0] == "S" or n2[0] == "S"):
                continue
            if n1 == n2:
                continue
            shortest_paths.append([p for p in nx.all_shortest_paths(g, source=n1, target=n2)])
    return shortest_paths


def get_all_graph_switches(g):
    return [str(s) for s in g.nodes() if s[0] == "S"]


class MPLS(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MPLS, self).__init__(*args, **kwargs)
        self.netfile = self.CONF.netfile
        self.switches = {}
        self.g = json_graph.node_link_graph(json.load(open(self.netfile)))
        self.switch_labels = get_all_graph_switches(self.g)
        self.logger.info("Switches " + str(self.switch_labels))
        self.connected_switches = []
        self.link_labels = defaultdict(list)
        self.lsps = {}  # Keep track of all the LSPs created

        self.nodes = self.g.nodes()
        self.logger.info(self.g.nodes())

        # print self.link_labels
        # nx.draw(self.g, with_labels=True)
        # p.show()
        # print self.show_all_lsps()

        if not self.CONF.notelnet:
            eventlet.spawn(backdoor.backdoor_server,
                           eventlet.listen(('localhost', 3000)))

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures)
    def switch_features(self, event):
        msg = event.msg
        dp = msg.datapath
        switchName = dpidDecode(dp.id)
        self.logger.info("Switch {} came up".format(switchName))
        self.logger.info("Masoud")
        self.switches[switchName] = dp  # Save switch information

        if switchName not in self.switch_labels:
            self.logger.info("Invalid Switch Connected")
            exit(0)

        self.connected_switches.append(switchName)
        self.logger.info("Connected Switches " + str(self.connected_switches))
        if len(self.connected_switches) == len(self.switch_labels):
            self.logger.info("All Switches Connected")
            self.make_all_lsps()

    def make_all_lsps(self):
        for paths in get_all_graph_paths(self.g):
            if len(paths) > 0:
                self.make_lsp(convert_array_to_path_string(paths[0]))

    def make_lsp(self, pathString):
        self.logger.info("make_path called with path {}".format(pathString))
        node_list = [str(p) for p in pathString.split("-")]
        # print node_list
        if not path_valid(self.g, node_list):
            self.logger.info("Invalid path, cannot create!")
            return
        if len(node_list) < 4:
            self.logger.info("No hop and single hops paths not supported")
            return
        fwd_path, fwd_labels = self._get_path_am(node_list)
        node_list.reverse()
        rev_path, rev_labels = self._get_path_am(node_list)
        self._setup_path(fwd_path)
        self._setup_path(rev_path)
        # self.logger.info("Forward flows: {}".format(fwd_path))
        # self.logger.info("Reverse flows: {}".format(rev_path))
        self.lsps[pathString] = {"fwd": fwd_path, "rev": rev_path,
                                 "fwd_labels": fwd_labels,
                                 "rev_labels": rev_labels}

    def show_all_lsps(self):
        self.logger.info("Currently {} bidirectional LSPs".format(len(self.lsps)))
        for pathString in list(self.lsps.keys()):
            self.logger.info("\t {}".format(pathString))

    def _setup_path(self, ma_path):
        for switch, flow in ma_path.items():
            datapath = self.switches[switch]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            # construct flow_mod message and send it.
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                 flow["actions"])]
            match = parser.OFPMatch(**flow["match_fields"])
            mod = parser.OFPFlowMod(datapath=datapath, priority=20,
                                    flags=ofproto.OFPFF_SEND_FLOW_REM,
                                    match=match, instructions=inst)
            datapath.send_msg(mod)  # Sends the actual message (finally!)

    def remove_lsp(self, pathString):
        if pathString not in list(self.lsps.keys()):
            self.logger.info("The path {} does not exist.".format(pathString))
            return
        lsp = self.lsps[pathString]
        self._remove_path(lsp["fwd"])  # Remove flow table entries forward
        self._remove_path(lsp["rev"])  # Remove flow table entries reverse
        for link, label in lsp["fwd_labels"].items():
            self.link_labels[link].remove(label)
        for link, label in lsp["rev_labels"].items():
            self.link_labels[link].remove(label)
        del self.lsps[pathString]

    def _remove_path(self, ma_path):
        self.logger.info("Remove path: {}".format(ma_path))
        for switch, flow in ma_path.items():
            datapath = self.switches[switch]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                 flow["actions"])]
            match = parser.OFPMatch(**flow["match_fields"])
            mod = parser.OFPFlowMod(datapath=datapath,
                                    command=ofproto.OFPFC_DELETE,
                                    table_id=ofproto.OFPTT_ALL,
                                    out_port=ofproto.OFPP_ANY,
                                    out_group=ofproto.OFPG_ANY,
                                    priority=20, match=match, instructions=inst)
            self.logger.info("sending fwd del to switch {} match {} inst {}".format(switch, match, inst))
            datapath.send_msg(mod)

    def _get_path_am(self, node_list):
        src = node_list[0]
        dst = node_list[-1]
        labels_used = {}
        switch_flows = OrderedDict()
        g = self.g
        datapath = self.switches[node_list[1]]
        ofproto = datapath.ofproto  # Gets the OpenFlow constants
        parser = datapath.ofproto_parser  # Gets the OpenFlow data structures
        label_list = self.link_labels[(node_list[1], node_list[2])]
        plabel = assign_label(label_list)
        labels_used[(node_list[1], node_list[2])] = plabel
        match_fields = {"in_port": get_in_port(g, node_list[0], node_list[1]),
                        "eth_type": 0x800,
                        "ipv4_src": g.node[src]['ip'],
                        "ipv4_dst": g.node[dst]['ip']}
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER),  # Debugging
                   parser.OFPActionPushMpls(),
                   parser.OFPActionSetField(mpls_label=plabel),
                   parser.OFPActionOutput(
                       get_out_port(g, node_list[1], node_list[2]))
                   ]
        switch_flows[node_list[1]] = {"match_fields": match_fields,
                                      "actions": actions}
        for i in range(2, len(node_list) - 1):
            datapath = self.switches[node_list[i]]
            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser
            match_fields = {
                "in_port": get_in_port(g, node_list[i - 1], node_list[i]),
                "eth_type": 0x8847,
                "mpls_label": plabel
            }
            if i < len(node_list) - 2:
                label_list = self.link_labels[(node_list[i], node_list[i + 1])]
                olabel = assign_label(label_list)
                labels_used[(node_list[i], node_list[i + 1])] = olabel
                actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER),  # for debugging
                           parser.OFPActionDecMplsTtl(),
                           parser.OFPActionSetField(mpls_label=olabel),
                           parser.OFPActionOutput(get_out_port(g, node_list[i],
                                                               node_list[
                                                                   i + 1]))]
                plabel = olabel  # output label becomes the next input label
            else:  # Last switch, we need to pop
                actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER),  # for debugging
                           parser.OFPActionPopMpls(),
                           parser.OFPActionOutput(get_out_port(g, node_list[i],
                                                               node_list[
                                                                   i + 1]))]
            switch_flows[node_list[i]] = {"match_fields": match_fields,
                                          "actions": actions}
        return switch_flows, labels_used

    @set_ev_cls(ofp_event.EventOFPPacketIn)
    def packet_in(self, event):
        """ Handles packets sent to the controller.
            Used for debugging."""
        msg = event.msg
        dp = msg.datapath
        # Assumes that datapath ID represents an ascii name
        switchName = dpidDecode(dp.id)
        packet = Packet(msg.data)
        # self.logger.info("packet: {}".format(msg))
        ether = packet.get_protocol(ryu.lib.packet.ethernet.ethernet)
        ethertype = ether.ethertype
        self.logger.info(" Switch {} received packet with ethertype: {}".format(switchName, hex(ethertype)))
        if ethertype == 0x8847:
            mpls = packet.get_protocol(ryu.lib.packet.mpls.mpls)
            self.logger.info("Label: {}, TTL: {}".format(mpls.label, mpls.ttl))
        ipv4 = packet.get_protocol(ryu.lib.packet.ipv4.ipv4)
        if ipv4:
            self.logger.info("IPv4 src: {} dst: {}".format(
                ipv4.src, ipv4.dst))


def assign_label(label_list):
    if not label_list:
        new_label = random.randint(1, 1000)
    else:
        new_label = random.randint(1, 1000)
        while new_label in label_list:
            new_label = random.randint(1, 1000)
    label_list.append(new_label)
    return new_label


def path_valid(g, p):
    plen = len(p)
    for i in range(plen - 1):
        if not g.has_edge(p[i], p[i + 1]):  # nice NetworkX graph feature.
            return False
    return True


def get_out_port(g, n1, n2):
    return g[n1][n2]["ports"][n1]


def get_in_port(g, n1, n2):
    return g[n1][n2]["ports"][n2]


def dpidDecode(aLong):
    try:
        myBytes = bytearray.fromhex('{:8x}'.format(aLong)).strip()
        return myBytes.decode()
    except ValueError:
        return str(aLong)


if __name__ == "__main__":
    manager.main(args=sys.argv)
