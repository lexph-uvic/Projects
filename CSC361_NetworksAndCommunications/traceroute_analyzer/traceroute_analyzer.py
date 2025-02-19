#!/usr/bin/python3.8
"""
Module Name: traceroute_analyzer.py
Author: Lex Phillips
Date: 2024-11-29

Main module for analyzing traceroutes from PCAP files.

Acknowledgments:
    - All docstrings were generated with Microsoft Copilot
      and validated/adjusted by author


This script processes packet capture (PCAP) files to identify probes, intermediate routers, and round-trip times (RTTs).
It can output the analysis to a file or print it to the console.

Functions:
- `requirement1`: Generates formatted traceroute analysis.
- `add_probe`: Adds probes to the collection, ensuring no duplicate keys.
- `main`: Main function for processing PCAP files and generating traceroute analysis.

Usage:
    python traceroute_analyzer.py <inputfile> [outputfile]
"""

import sys
from collections import namedtuple

# Local imports
from protocol_enums import TransportProtocol
from pcap_packet_factory import PcapPacketFactory
from traceroute import Probe, FragmentedDatagram, ProbeAnswer, TraceRoute


def requirement1(traceroute, reassembled_datagrams, protocols):
    """
    Generate formatted analysis output for traceroute data.

    Parameters:
        traceroute (TraceRoute): Processed traceroute data.
        reassembled_datagrams (set): Unique fragmentation structures.
        protocols (set): Protocols encountered during analysis.

    Returns:
        str: Formatted analysis output.
    """
    indent = '      '  # Define indentation for formatting
    output = []

    # Source and destination IPs
    output.append(f"The IP address of the source node: {traceroute.src_ip}")
    output.append(f"The IP address of ultimate destination node: {traceroute.dest_ip}")

    # Intermediate nodes
    output.append(f"The IP addresses of the intermediate destination nodes:")
    if traceroute.intermediates:
        intermediate_output = "\n".join(
            f"{indent}{('router ' + str(count + 1) + ':'):<12}"
            f"{intermediate['router_ip']:<18}Hop:{intermediate['hop']:<8}"
            for count, intermediate in enumerate(traceroute.intermediates)
            if intermediate['router_ip'] != traceroute.dest_ip  # Exclude destination IP
        )
        if intermediate_output:
            output.append(intermediate_output)
        else:
            output.append(f"{indent}No intermediate nodes found.")
    else:
        output.append(f"{indent}No intermediate nodes found.")

    output.append("")  # Add an empty line

    # Protocols
    output.append("The values in the protocol field of IP headers:")
    if protocols:
        protocol_output = "\n".join(
            f"{indent}{protocol.value}: {protocol.name}" 
            for protocol in protocols
        )
        output.append(protocol_output)
    else:
        output.append(f"{indent}No protocols found in the IP headers.")

    output.append("")  # Add an empty line

    # Fragmented datagrams
    if reassembled_datagrams:
        output.append("Unique fragmentation structures:")
        for datagram_info in reassembled_datagrams:
            output.append(f"The number of fragments created from the original datagram is: {datagram_info.fragment_count}")
            output.append(f"The offset of the last fragment is: {datagram_info.final_fragment_offset}")
    else:
        output.append("No fragmented datagrams found.")

    output.append("")  # Add an empty line
    
    # Statistics
    if traceroute.statistics:
        statistics_output = "\n".join(
            f"{indent}The avg RTT between {traceroute.src_ip} and {stat['router_ip']} is: "
            f"{stat['avg_rtt']:.2f} ms, the s.d. is: {stat['std_dev']:.2f} ms"
            for stat in traceroute.statistics
        )
        output.append(statistics_output)
    else:
        output.append(f"{indent}No RTT statistics available.")

    return "\n".join(output)


def add_probe(probe, probes):
    """
    Add a probe to the collection, ensuring no duplicate keys.

    Parameters:
        probe (Probe): The probe object to add.
        probes (dict): Dictionary of existing probes.

    Raises:
        ValueError: If a duplicate probe key is detected.
    """
    if probe.key not in probes:
        probes[probe.key] = ProbeAnswer(probe)
    else:
        raise ValueError(f"Duplicate probe keys detected: {probe.key}")


def main(outputfilename=None):
    """
    Main function to analyze traceroutes from a PCAP file.

    Parameters:
        outputfilename (str, optional): Filepath to write the output. If not provided, prints to the console.
    """
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename> [outputfilename]")
        sys.exit(1)

    filename = sys.argv[1]
    outputfilename = sys.argv[2] if len(sys.argv) > 2 else outputfilename

    try:
        with open(filename, 'rb') as f:
            packet_factory = PcapPacketFactory(f)
            probes = {}
            pcap_packet_answers = []
            fragmented_datagrams = {}
            reassembled_datagrams = set()
            protocols_used = set()
            FragmentedDatagramInfo = namedtuple('FragmentedDatagramInfo', ['fragment_count', 'final_fragment_offset'])

            # Parse packets
            for count, pcap_packet in enumerate(packet_factory):
                if pcap_packet is None or pcap_packet.network_header is None:
                    continue

                # Handle fragmented datagrams
                if Probe.is_fragmented(pcap_packet):
                    frag_key = FragmentedDatagram.generate_key(pcap_packet)
                    if frag_key not in fragmented_datagrams:
                        fragmented_datagrams[frag_key] = FragmentedDatagram(pcap_packet)
                    else:
                        datagram = fragmented_datagrams[frag_key]
                        complete_probe = datagram.add_fragment(pcap_packet)
                        if complete_probe:
                            protocols_used.add(TransportProtocol(pcap_packet.network_header.get("protocol")))
                            add_probe(complete_probe, probes)
                            fc = len(datagram.fragments)
                            ff_offset = datagram.last_offset
                            reassembled_datagrams.add(FragmentedDatagramInfo(fragment_count=fc, final_fragment_offset=ff_offset))
                            del fragmented_datagrams[frag_key]
                    continue

                # Handle non-fragmented probes
                if Probe.is_probe(pcap_packet):
                    protocols_used.add(TransportProtocol(pcap_packet.network_header.get("protocol")))
                    probe = Probe.from_packet(pcap_packet, is_probe=True)
                    add_probe(probe, probes)

                # Handle answers
                elif Probe.is_answer(pcap_packet):
                    protocols_used.add(TransportProtocol(pcap_packet.network_header.get("protocol")))
                    pcap_packet_answers.append(pcap_packet)

            # Add answers to probes
            for answer_packet in pcap_packet_answers:
                probe_key = Probe.generate_key(answer_packet, is_probe=False)
                answer = Probe.from_packet(answer_packet, is_probe=False)
                answer.set_key = probe_key
                if probe_key in probes:
                    probes[probe_key].add_answer(answer)

            traceroute = TraceRoute(probes)

            output1 = requirement1(traceroute, reassembled_datagrams, protocols_used)
            if output1:
                if outputfilename:
                    with open(outputfilename, 'w') as outfile:
                        outfile.write(output1)
                else:
                    print(output1)

    except Exception as e:
        print(f'Error: {e}')


if __name__ == "__main__":
    main()
