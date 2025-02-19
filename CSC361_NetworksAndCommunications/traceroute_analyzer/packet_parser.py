"""Module for parsing network packets at various protocol layers: Ethernet, IPv4, TCP, etc."""

import struct

NETWORK_BYTE_ORDER = '!'  # Network byte order (Big-endian)
ETHERNET_HEADER_SIZE = 14

# =================== Utilities =======================

def format_mac_address(mac_bytes):
    """Convert raw MAC address bytes to a human-readable hexadecimal format."""
    return ':'.join(f'{b:02x}' for b in mac_bytes)


def format_ip_address(raw_ip):
    """Convert raw IP address bytes to dotted decimal notation."""
    return '.'.join(map(str, raw_ip))


# =================== Global Header Parser =======================

class GlobalHeaderParser:
    """Parse the global header of a pcap file to determine byte order and metadata."""

    @staticmethod
    def parse(data):
        """Parse the pcap global header to determine byte order, timestamp precision, and metadata fields."""
        if len(data) < 24:
            raise ValueError("Insufficient data for global header")

        # Unpack the magic number
        magic_number = struct.unpack('>I', data[:4])[0]

        # Determine byte order and timestamp precision
        if magic_number == 0xa1b2c3d4:  # Big-endian, microsecond resolution
            global_order = '>'
            timestamp_precision = 'microseconds'
        elif magic_number == 0xd4c3b2a1:  # Little-endian, microsecond resolution
            global_order = '<'
            timestamp_precision = 'microseconds'
        elif magic_number == 0xa1b23c4d:  # Big-endian, nanosecond resolution
            global_order = '>'
            timestamp_precision = 'nanoseconds'
        elif magic_number == 0x4d3cb2a1:  # Little-endian, nanosecond resolution
            global_order = '<'
            timestamp_precision = 'nanoseconds'
        elif magic_number == 0x0a0d0d0a:
            raise ValueError("pcap Next Generation format not supported")
        else:
            raise ValueError("Unrecognized file format")

        # Unpack the rest of the global header
        version_major, version_minor, thiszone, sigfigs, snaplen, network = struct.unpack(
            global_order + 'HHIIII', data[4:24]
        )

        # Return parsed global header metadata
        return {
            "byte_order": global_order,
            "timestamp_precision": timestamp_precision,
            "version_major": version_major,
            "version_minor": version_minor,
            "thiszone": thiszone,
            "sigfigs": sigfigs,
            "snaplen": snaplen,
            "network": network,
        }



# =================== Link Layer Parsers =======================

class EthernetParser:
    """Parse the Ethernet header to extract source and destination MAC addresses."""

    def parse(self, data):
        if len(data) < ETHERNET_HEADER_SIZE:
            raise ValueError("Insufficient data for Ethernet header")

        ethernet_fields = struct.unpack(NETWORK_BYTE_ORDER + '6s6sH', data[:ETHERNET_HEADER_SIZE])
        payload = data[ETHERNET_HEADER_SIZE:]
        metadata = {
            "dest_mac": format_mac_address(ethernet_fields[0]),
            "src_mac": format_mac_address(ethernet_fields[1]),
            "network_type": ethernet_fields[2],
        }
        return {"metadata": metadata, "payload": payload}


link_layer_parsers = {
    1: EthernetParser(),  # 1 represents Ethernet
}


# =================== Network Layer Parsers =======================

class IPv4Parser:
    """Parse the IPv4 header to extract version, IHL, flags, and address information."""

    def parse(self, data):
        if len(data) < 20:  # Minimum IPv4 header size
            raise ValueError("Insufficient data for IPv4 header")

        # Parse version and IHL (first byte)
        version_ihl = struct.unpack('B', data[0:1])[0]
        version = version_ihl >> 4
        ihl = version_ihl & 0x0F
        header_len = ihl * 4

        if len(data) < header_len:
            raise ValueError("Insufficient data for full IPv4 header")

        # Parse the rest of the IPv4 fields
        ipv4_fields = struct.unpack(NETWORK_BYTE_ORDER + 'BHHHBBH4s4s', data[1:20])

        # Extract flags and fragment offset
        flags_fragment_offset = ipv4_fields[3]
        flags = (flags_fragment_offset >> 13) & 0x07
        fragment_offset = flags_fragment_offset & 0x1FFF

        flags_dict = {
            "mf": bool((flags >> 0) & 0x01),  # More Fragments
            "df": bool((flags >> 1) & 0x01),  # Don't Fragment
        }

        metadata = {
            "version": version,
            "ihl": ihl,
            "tos": ipv4_fields[0],
            "total_length": ipv4_fields[1],
            "identification": ipv4_fields[2],
            "flags": flags_dict,
            "fragment_offset": fragment_offset,
            "ttl": ipv4_fields[4],
            "protocol": ipv4_fields[5],
            "header_checksum": ipv4_fields[6],
            "src_ip": format_ip_address(ipv4_fields[7]),
            "dest_ip": format_ip_address(ipv4_fields[8]),
            "header_size": ihl * 4,
        }

        payload = data[header_len:]
        return {"metadata": metadata, "payload": payload}


network_layer_parsers = {
    0x0800: IPv4Parser(),  # IPv4 EtherType
}


# =================== Transport Layer Parsers =======================

class ICMPParser:
    """Parse the ICMP header to extract type, code, checksum, and additional fields."""

    def parse(self, data):
        if len(data) < 8:  # Minimum ICMP header size
            raise ValueError("Insufficient data for ICMP header")

        # Parse the common ICMP fields
        icmp_fields = struct.unpack(NETWORK_BYTE_ORDER + 'BBH', data[:4])
        icmp_type, icmp_code, checksum = icmp_fields

        metadata = {
            "icmp_type": icmp_type,
            "icmp_code": icmp_code,
            "checksum": checksum,
        }

        # Additional parsing based on ICMP type
        if icmp_type in {8, 0}:  # Echo Request or Echo Reply
            # Parse Identifier and Sequence Number
            if len(data) >= 8:
                identifier, sequence_number = struct.unpack(NETWORK_BYTE_ORDER + 'HH', data[4:8])
                metadata.update({
                    "identifier": identifier,
                    "sequence_number": sequence_number,
                })
            payload = data[8:]  # Remaining data as payload

        elif icmp_type in {3, 11}:  # Destination Unreachable or Time Exceeded
            # Embedded IP header and payload
            payload = data[8:]  # Contains offending packet's IP header and beyond
            metadata["embedded_data"] = payload

        else:
            # For other ICMP types, treat remaining data as payload
            payload = data[4:]  # Remaining data as payload

        return {"metadata": metadata, "payload": payload}
    

class TCPParser:
    """Parse the TCP header to extract port information, sequence/ack numbers, and flags."""

    def parse(self, data):
        if len(data) < 20:  # Minimum TCP header size
            raise ValueError("Insufficient data for TCP header")

        tcp_fields = struct.unpack(NETWORK_BYTE_ORDER + 'HHIIHHHH', data[:20])
        data_offset = (tcp_fields[4] >> 12) & 0x0F
        header_len = data_offset * 4

        if len(data) < header_len:
            raise ValueError("Insufficient data for full TCP header")

        # Parse individual TCP flags
        flags = tcp_fields[4] & 0x01FF
        flags_dict = {
            "ns": bool((flags >> 8) & 0x01),
            "cwr": bool((flags >> 7) & 0x01),
            "ece": bool((flags >> 6) & 0x01),
            "urg": bool((flags >> 5) & 0x01),
            "ack": bool((flags >> 4) & 0x01),
            "psh": bool((flags >> 3) & 0x01),
            "rst": bool((flags >> 2) & 0x01),
            "syn": bool((flags >> 1) & 0x01),
            "fin": bool((flags >> 0) & 0x01),
        }

        metadata = {
            "src_port": tcp_fields[0],
            "dest_port": tcp_fields[1],
            "seq_number": tcp_fields[2],
            "ack_number": tcp_fields[3],
            "data_offset": data_offset,
            "flags": flags_dict,
            "window_size": tcp_fields[5],
            "checksum": tcp_fields[6],
            "urgent_pointer": tcp_fields[7],
        }

        payload = data[header_len:]
        return {"metadata": metadata, "payload": payload}
    

class UDPParser:
    """Parse the UDP header to extract source/destination ports, length, and checksum."""

    def parse(self, data):
        if len(data) < 8:  # Minimum UDP header size
            raise ValueError("Insufficient data for UDP header")

        # Parse the UDP header
        udp_fields = struct.unpack(NETWORK_BYTE_ORDER + 'HHHH', data[:8])
        metadata = {
            "src_port": udp_fields[0],
            "dest_port": udp_fields[1],
            "length": udp_fields[2],  # Length includes header + payload
            "checksum": udp_fields[3],
        }

        # Remaining data after the UDP header is the payload
        payload = data[8:]
        return {"metadata": metadata, "payload": payload}


transport_layer_parsers = {
    1: ICMPParser(),  # ICMP protocol number
    6: TCPParser(),  # TCP protocol number
    17: UDPParser(),  # UDP protocol number
    
}


