#!/usr/bin/python3.8
"""
Module Name: packet_sniffer.py
Author: Lex Phillips
Date: 2024-10-28

Main module for analyzing TCP connections in pcap files.

Acknowledgments:
    - All docstrings were generated with Microsoft Copilot
      and validated/adjusted by author
"""

import sys
import struct
from datetime import datetime, timedelta

# Local imports
from packet_parser import GlobalHeaderParser, link_layer_parsers, network_parsers, transport_parsers
from connection import Packet, Connection
from cap_analysis import AnalyzeConnections

ETHERNET_HEADER_SIZE = 14
DEBUG_FILE = 'debug.txt'


def parse_packet(packet_data):
    """Parse Ethernet/IPv4/TCP packet and return headers if successful."""
    
    ethernet_parser = link_layer_parsers.get(1)
    ethernet_header = ethernet_parser.parse(packet_data)

    eth_type = ethernet_header.get("eth_type")
    if eth_type != 0x0800:
        return None

    ipv4_parser = network_parsers.get(eth_type)
    ipv4_header = ipv4_parser.parse(packet_data[ETHERNET_HEADER_SIZE:]) if ipv4_parser else None
    if not ipv4_header or ipv4_header.get("protocol") != 6:  # Protocol 6 is TCP
        return None

    tcp_parser = transport_parsers.get(ipv4_header["protocol"])
    if tcp_parser:
        offset = ETHERNET_HEADER_SIZE + (ipv4_header.get("ihl") * 4)
        tcp_header = tcp_parser.parse(packet_data[offset:])
        if tcp_header:
            return ethernet_header, ipv4_header, tcp_header
    return None


def connection_summary(key, connection, connection_number):
    """Generate a formatted summary string for a connection."""
    summary = []

    if connection_number == 1:
        summary.append("B) Connections' details:\n")

    summary.append(f"Connection {connection_number}:")
    src_ip, src_port, dest_ip, dest_port = key
    indent = ' ' * 4
    summary.extend([
        f"{indent}Source Address: {src_ip}",
        f"{indent}Destination Address: {dest_ip}",
        f"{indent}Source Port: {src_port}",
        f"{indent}Destination Port: {dest_port}"
    ])

    reset = '/R' if connection.has_rst else ''
    status = f"S{connection.SYN_count}F{connection.FIN_count}{reset}"
    summary.append(f"{indent}Status: {status}")

    if connection.is_complete:
        summary.extend([
            f"{indent}Start Time: {connection.start_time:.6f} seconds",
            f"{indent}End Time: {connection.end_time:.6f} seconds",
            f"{indent}Duration: {connection.duration:.6f} seconds",
            f"{indent}Number of packets sent from Source to Destination: {connection.flow_ab.get_packet_count()}",
            f"{indent}Number of packets sent from Destination to Source: {connection.flow_ba.get_packet_count()}",
            f"{indent}Total number of packets: {connection.flow_ab.get_packet_count() + connection.flow_ba.get_packet_count()}",
            f"{indent}Number of data bytes sent from Source to Destination: {connection.flow_ab.total_bytes}",
            f"{indent}Number of data bytes sent from Destination to Source: {connection.flow_ba.total_bytes}",
            f"{indent}Total number of data bytes: {connection.total_bytes}"
        ])

    summary.append("END")
    summary.append("+++++++++++++++++++++++++++++++++")
    return "\n".join(summary)


def general_summary(analysis):
    """Return a general summary of TCP connections statistics."""
    return (
        f"\nC) General\n\n"
        f"The total number of complete TCP connections: {analysis.complete_connections}\n"
        f"The number of reset TCP connections: {analysis.reset_connections}\n"
        f"The number of TCP connections that were still open when the trace capture ended: {analysis.open_connections_after}\n"
        f"The number of TCP connections established before the capture started: {analysis.open_connections_before}\n"
    )


def complete_connections_summary(analysis):
    """Return a summary of complete TCP connections statistics."""
    return (
        f"D) Complete TCP connections:\n\n"
        f"Minimum time duration: {analysis.min_duration:.6f} seconds\n"
        f"Mean time duration: {analysis.mean_duration:.6f} seconds\n"
        f"Maximum time duration: {analysis.max_duration:.6f} seconds\n\n"
        f"Minimum RTT value: {analysis.min_rtt:.6f}\n"
        f"Mean RTT value: {analysis.mean_rtt:.6f}\n"
        f"Maximum RTT value: {analysis.max_rtt:.6f}\n\n"
        f"Minimum number of packets including both send/received: {analysis.min_packet_count}\n"
        f"Mean number of packets including both send/received: {analysis.mean_packet_count:.6f}\n"
        f"Maximum number of packets including both send/received: {analysis.max_packet_count}\n\n"
        f"Minimum receive window size including both send/received: {analysis.min_window_size}\n"
        f"Mean receive window size including both send/received: {analysis.mean_window_size:.6f}\n"
        f"Maximum receive window size including both send/received: {analysis.max_window_size}\n"
    )


def main():
    """Main function for analyzing TCP connections from a pcap file."""
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        with open(filename, 'rb') as f, open(DEBUG_FILE, 'w') as debug:
            global_header = GlobalHeaderParser.parse(f.read(24))
            connections = {}
            base_timestamp = None

            while packet_header := f.read(16):
                ts_sec, ts_usec, incl_len, orig_len = struct.unpack(global_header["byte_order"] + 'IIII', packet_header)
                timestamp = datetime.fromtimestamp(ts_sec) + timedelta(microseconds=ts_usec)
                if base_timestamp is None:
                    base_timestamp = timestamp
                relative_time = (timestamp - base_timestamp).total_seconds()
                packet_data = f.read(incl_len)

                if global_header["network"] == 1:  # Ethernet
                    result = parse_packet(packet_data)
                    if result:
                        ethernet_header, ipv4_header, tcp_header = result
                        offset = ETHERNET_HEADER_SIZE + (ipv4_header.get("ihl") * 4) + (tcp_header.get("data_offset") * 4)
                        payload_end = ETHERNET_HEADER_SIZE + ipv4_header.get("total_length")
                        payload = packet_data[offset:payload_end] if offset < payload_end else b''
                        packet = Packet(ethernet_header, ipv4_header, tcp_header, relative_time, payload)
                        conn_key = packet.get_direction()
                        reverse_key = packet.get_opposite_direction()
                        connection = connections.get(conn_key) or connections.get(reverse_key)

                        if not connection:
                            connections[conn_key] = Connection(packet)
                        else:
                            connection.add_packet(packet)

            analysis = AnalyzeConnections(connections)
            section_divider = '_______________________________________\n'
            print(f"A) Total number of connections: {len(connections)}")
            print(section_divider)

            for count, (conn_key, conn) in enumerate(connections.items(), 1):
                print(connection_summary(conn_key, conn, count))

            print(general_summary(analysis))
            print(section_divider)
            print(complete_connections_summary(analysis))
            print(section_divider)

    except (FileNotFoundError, IOError) as e:
        print(f"Error reading file: {e}")
    except ValueError as e:
        print(f"ValueError: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
