"""Module for parsing network packets at various protocol layers: Ethernet, IPv4, TCP, etc."""

import struct

NETWORK_BYTE_ORDER = '!'  # Network byte order (Big-endian)
ETHERNET_HEADER_SIZE = 14

# =================== Global Parser =======================

class GlobalHeaderParser:
    """Parse the global header of a pcap file to determine byte order and metadata."""

    @staticmethod
    def parse(data):
        """Parse the pcap global header to determine byte order and metadata fields."""
        magic_number = struct.unpack('>I', data[:4])[0]
        if magic_number == 0xa1b2c3d4:
            global_order = '>'  # Big-endian
        elif magic_number == 0xd4c3b2a1:
            global_order = '<'  # Little-endian
        elif magic_number == 0x0a0d0d0a:
            raise ValueError("pcap Next Generation format not supported")
        else:
            raise ValueError("Unrecognized file format")

        version_major, version_minor, thiszone, sigfigs, snaplen, network = struct.unpack(
            global_order + 'HHIIII', data[4:]
        )
        return {
            "byte_order": global_order,
            "version_major": version_major,
            "version_minor": version_minor,
            "thiszone": thiszone,
            "sigfigs": sigfigs,
            "snaplen": snaplen,
            "network": network,
        }


# ======== LINK LAYER (DATA LINK LAYER) PARSERS ===========

class EthernetParser:
    """Parse the Ethernet header to extract source and destination MAC addresses."""

    def parse(self, data):
        ethernet_fields = struct.unpack(NETWORK_BYTE_ORDER + '6s6sH', data[:ETHERNET_HEADER_SIZE])
        return {
            "dest_mac": self.format_mac_address(ethernet_fields[0]),
            "src_mac": self.format_mac_address(ethernet_fields[1]),
            "eth_type": ethernet_fields[2],
        }

    @staticmethod
    def format_mac_address(mac_bytes):
        """Convert raw MAC address bytes to a human-readable hexadecimal format."""
        return ':'.join(f'{b:02x}' for b in mac_bytes)


link_layer_parsers = {
    1: EthernetParser(),  # 1 represents Ethernet
}


# ================= NETWORK LAYER PARSERS ==================

class IPv4Parser:
    """Parse the IPv4 header to extract version, IHL, flags, and address information."""

    def parse(self, data):
        # Parse version and IHL (first byte)
        version_ihl = struct.unpack('B', data[0:1])[0]
        version = version_ihl >> 4
        ihl = version_ihl & 0x0F
        header_len = ihl * 4

        if len(data) < header_len:
            raise ValueError("Insufficient data for IPv4 header")

        # Parse the rest of the IPv4 fields
        ipv4_fields = struct.unpack(NETWORK_BYTE_ORDER + 'BHHHBBH4s4s', data[1:20])

        # Extract flags and fragment offset
        flags_fragment_offset = ipv4_fields[3]
        flags = (flags_fragment_offset >> 12) & 0x0F
        fragment_offset = flags_fragment_offset & 0x0FFF

        ipv4_header = {
            "version": version,
            "ihl": ihl,
            "tos": ipv4_fields[0],
            "total_length": ipv4_fields[1],
            "identification": ipv4_fields[2],
            "flags": flags,
            "fragment_offset": fragment_offset,
            "ttl": ipv4_fields[4],
            "protocol": ipv4_fields[5],
            "header_checksum": ipv4_fields[6],
            "src_ip": self.format_ip_address(ipv4_fields[7]),
            "dest_ip": self.format_ip_address(ipv4_fields[8]),
        }

        # Include options if present
        if header_len > 20:
            ipv4_header["options"] = data[20:header_len]

        return ipv4_header

    @staticmethod
    def format_ip_address(raw_ip):
        """Convert raw IP address bytes to dotted decimal notation."""
        return '.'.join(map(str, raw_ip))


class IPv6Parser:
    def parse(self, data):
        pass


class ARPParser:
    def parse(self, data):
        pass


network_parsers = {
    0x0800: IPv4Parser(),  # IPv4 EtherType
    0x0806: ARPParser(),   # ARP EtherType
    0x86DD: IPv6Parser(),  # IPv6 EtherType
}


# ================ TRANSPORT LAYER PARSERS =================

class TCPParser:
    """Parse the TCP header to extract port information, sequence/ack numbers, and flags."""

    def parse(self, data):
        tcp_fields = struct.unpack(NETWORK_BYTE_ORDER + 'HHIIHHHH', data[0:20])
        data_offset = (tcp_fields[4] >> 12) & 0x0F
        reserved = (tcp_fields[4] >> 9) & 0x07
        flags = tcp_fields[4] & 0x1FF
        header_len = data_offset * 4

        # Parse individual TCP flags
        flags_dict = {
            "ns": (flags >> 8) & 0x01,
            "cwr": (flags >> 7) & 0x01,
            "ece": (flags >> 6) & 0x01,
            "urg": (flags >> 5) & 0x01,
            "ack": (flags >> 4) & 0x01,
            "psh": (flags >> 3) & 0x01,
            "rst": (flags >> 2) & 0x01,
            "syn": (flags >> 1) & 0x01,
            "fin": flags & 0x01,
        }
        
        tcp_header = {
            "src_port": tcp_fields[0],
            "dest_port": tcp_fields[1],
            "seq_number": tcp_fields[2],
            "ack_number": tcp_fields[3],
            "data_offset": data_offset,
            "reserved": reserved,
            "flags": flags_dict,
            "window_size": tcp_fields[5],
            "checksum": tcp_fields[6],
            "urgent_pointer": tcp_fields[7],
        }

        # Include options if present
        if header_len > 20:
            tcp_header["options"] = data[20:header_len]

        return tcp_header


class UDPParser:
    def parse(self, data):
        pass


transport_parsers = {
    6: TCPParser(),  # TCP protocol number
    17: UDPParser(),  # UDP protocol number
}
