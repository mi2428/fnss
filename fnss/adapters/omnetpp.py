"""Omnet++ adapter

This module contains the code for converting an FNSS topology object into a NED
script to deploy such topology into Omnet++.
"""
from warnings import warn

from fnss.units import time_units, capacity_units


__all__ = ['to_omnetpp']


# Template text rendered by the template engine
__TEMPLATE = r"""// Code generated by Fast Network Simulator Setup (FNSS)
<%
import re
from fnss.units import time_units, capacity_units
from fnss.netconfig.nodeconfig import get_stack, \
                                      get_application_names, \
                                      get_application_properties

# Convert capacity in Mb
if set_capacities:
    capacity_norm = capacity_units[topology.graph['capacity_unit']] / 1000000.0
# Convert delay it in ms
if set_delays:
    delay_norm = time_units[topology.graph['delay_unit']]

# Get topology name
name = topology.name
name = "net" if name == "" else re.sub("[^A-Za-z0-9]", "_", name).strip(" _")

# Get numerical ID of a node
nodes = topology.nodes()
node_map = dict((nodes[i], i) for i in range(len(nodes)))

%>
// This is the module modelling the nodes of network
module node {
    //TODO: Implement it
}

// Create network
network ${name} {
    connections allowunconnected:
% for u, v in topology.edges_iter():
    <%
    attr_str = ""
    if set_delays:
        delay = delay_norm * topology.edge[u][v]['delay']
        attr_str += " delay=%sms;" % (str(delay))
    if set_capacities:
        capacity = capacity_norm * topology.edge[u][v]['capacity']
        attr_str += " datarate=%sMbps;" % (str(capacity))
    %>
    ${"node[%s].ppg$o++ --> {%s} --> node[%s].pppg$i++;" % (str(node_map[u]), attr_str.strip(), str(node_map[v]))}
    % if not topology.is_directed():
    ${"node[%s].ppg$i++ <-- {%s} <-- node[%s].pppg$o++;" % (str(node_map[u]), attr_str.strip(), str(node_map[v]))}
    % endif
% endfor
}
"""

def to_omnetpp(topology, path=None):
    """Convert an FNSS topology into an Omnet++ NED script.

    Parameters
    ----------
    topology : Topology
        The topology object to convert
    path : str, optional
        The path to the output NED file.
        If not specified, prints to standard output
    """
    try:
        from mako.template import Template
    except ImportError:
        raise ImportError('Cannot import mako.template module. '
                          'Make sure mako is installed on this machine.')
    set_delays = True
    set_capacities = True
    # Check correctness of capacity and delay attributes
    if not 'capacity_unit' in topology.graph or not topology.graph['capacity_unit'] in capacity_units:
        warn('Missing or invalid capacity unit attribute in the topology. The '
             'output file will be generated without link capacity attributes.')
        set_capacities = False
    if not 'delay_unit' in topology.graph or not topology.graph['delay_unit'] in time_units:
        warn('Missing or invalid delay unit attribute in the topology. The '
             'output file will be generated without link delay attributes.')
        set_delays = False
    template = Template(__TEMPLATE)
    variables = {
        'topology':        topology,
        'set_capacities':  set_capacities,
        'set_delays':      set_delays,
                }
    ned = template.render(**variables)
    if path:
        with open(path, "w") as out:
            out.write(ned)
    else:
        print(ned)
