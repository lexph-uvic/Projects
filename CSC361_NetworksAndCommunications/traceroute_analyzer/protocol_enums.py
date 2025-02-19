"""
Module defining enums for protocol types across data link, network, transport, and ICMP layers.
These enums are used to identify and categorize packet headers in PCAP parsing.
"""

from enum import Enum

class DataLinkType(Enum):
    """
    Enumeration of data link layer protocol types.
    """
    ETHERNET = 1  # Ethernet protocol
    WIFI = 105    # Wi-Fi protocol

class NetworkProtocol(Enum):
    """
    Enumeration of network layer protocol types.
    """
    IPv4 = 0x0800  # Internet Protocol version 4
    IPv6 = 0x86DD  # Internet Protocol version 6

class TransportProtocol(Enum):
    """
    Enumeration of transport layer protocol types.
    """
    TCP = 6   # Transmission Control Protocol
    UDP = 17  # User Datagram Protocol
    ICMP = 1  # Internet Control Message Protocol

class ICMPType(Enum):
    """
    Enumeration of ICMP message types.
    """
    REPLY = 0          # Echo Reply
    UNREACHABLE = 3    # Destination Unreachable
    REQUEST = 8        # Echo Request
    EXCEEDED = 11      # Time Exceeded

class ICMPCode(Enum):
    """
    Enumeration of ICMP-specific codes for certain message types.
    """
    # Codes for Destination Unreachable (Type 3)
    NETWORK_UNREACHABLE = 0  # Network Unreachable
    HOST_UNREACHABLE = 1     # Host Unreachable

    # Codes for Time Exceeded (Type 11)
    TTL_EXCEEDED = 0         # TTL Exceeded in Transit
    FRAGMENT_REASSEMBLY = 1  # Fragment Reassembly Time Exceeded
