import json
import re
import random

# Structure of node properties as JSON downloaded from iot-lab.info
# {"uid":"9378","archi":"m3:at86rf231","x":"62.26","y":"0.94","z":"-0.04",
#  "mobile":0,"camera":0,"site":"grenoble","state":"Busy",
#  "network_address":"m3-358.grenoble.iot-lab.info","mobility_type":" "}

class Testbed:
    def __init__(self, node_ids, site, archi, json_file, randomize=False):
        self.node_ids = node_ids
        self.site = site
        self.archi = archi
        self.json_file = json_file
        self.randomize = randomize
        self.filtered_json = self.__filter_json()
        self.nodes = self.__add_nodes()

    def get_deployment_struct_string(self):
        # What we want:
        # const struct id_mac deployment_fit[] = {
        #  { 0x01, {{0x02,0x00,0x00,0x00,0x00,0x00,0x93,0x78}}}, // 358
        #  { 0x02, {{0x02,0x00,0x00,0x00,0x00,0x00,0x92,0x82}}}, // 328
        #  ...
        #  { 0x11, {{0x02,0x00,0x00,0x00,0x00,0x00,0xb5,0x69}}}, // 298
        #  { 0,    {{0}}}
        # };
        deployment_struct =  "const struct id_mac deployment_fit[] = {\n"
        for node in self.nodes:
            node_line = "  { 0x" + hex(node.deployment_id)[2:].zfill(2) + \
                        ", {{" + node.link_layer_address_string + \
                        "}}}, // " + str(node.id)
            deployment_struct += node_line + "\n"
        deployment_struct += "  { 0,    {{0}}}\n"
        deployment_struct += "};"
        return deployment_struct   

    def get_argument_string(self):
        argument_string = ""
        for node in self.node_ids:
            argument_string += str(node) + "+"
        return argument_string[:-1]

    def __filter_json(self):
        with open(self.json_file) as nodes_json_file:
            nodes_json = json.load(nodes_json_file)

        filtered_json = []
        for node in nodes_json:
            if node["site"] == self.site and node["archi"] == self.archi:
                for node_id in self.node_ids:
                    if str(node_id) in node["network_address"]:
                        filtered_json.append(node)
        return filtered_json

    def __add_nodes(self):
        nodes = []
        deployment_ids = list(range(1, len(self.node_ids)+1))
        if self.randomize:
            random.shuffle(deployment_ids)
        for i, node_id in enumerate(self.node_ids):
            node_json = self.__find_node_in_json(self.filtered_json, node_id)
            if node_json is not None:
                nodes.append(Node(node_json, node_id, deployment_ids[i]))
            else:
                print("Unable to find node in json")
        return nodes

    def __find_node_in_json(self, nodes_json, node_id):
        for node_json in nodes_json:
            node_id_string = "-" + str(node_id) + "."
            if node_id_string in node_json["network_address"]:
                return node_json
        return None

class Node:
    def __init__(self, node_json, node_id, deployment_id):
        self.id = node_id
        self.deployment_id = deployment_id
        self.link_layer_address_string = \
            self.make_node_link_layer_addr_string(node_json)

    def findNodeId(self, node):
        result = \
            re.search(r".*-(\d*)\..*\.iot-lab\.info", node["network_address"])
        if result:
            return int(result.group(1))
        else:
            return 0

    def make_node_link_layer_addr_string(self, node):
        # We want the address as a string of comma-separated hexes:
        # 0x02,0x00,0x00,0x00,0x00,0x00,0x93,0x78
        uid_msb = "0x" + node["uid"][:2]
        uid_lsb = "0x" + node["uid"][2:]
        return "0x02,0x00,0x00,0x00,0x00,0x00," + uid_msb + "," + uid_lsb

def main():
    # Node IDs to use for experiment
    # See e.g. https://www.iot-lab.info/testbed/status
    node_ids = [1,  4,  5,  8,   9, 11, 39, 64, 61, 60,
                57, 56, 53, 48, 29, 20, 22, 34, 32, 36,
                37, 24, 52, 50, 10, 62]

    # Site name
    site = "strasbourg"

    # Node architecture, see https://www.iot-lab.info/testbed/status
    archi = "m3:at86rf231"

    # File with all node properties
    # Downloaded from https://www.iot-lab.info/testbed/status
    iotlab_nodes_json = "iotlab-nodes.json"

    print("Operating on " + str(len(node_ids)) + " nodes")

    # Set randomize=True to have deployment IDs be random
    testbed = Testbed(node_ids, site, archi, iotlab_nodes_json, randomize=False)

    print("\nContiki-ng deployment struct:")
    print(testbed.get_deployment_struct_string())
    print("\nIoT-LAB CLI nodes argument:")
    print(testbed.get_argument_string())

main()
