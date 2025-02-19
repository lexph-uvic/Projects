"""
Module for parsing PCAP files, extracting headers and payloads from captured packets.
Includes classes for reading PCAP files (`PcapPacketFactory`) and representing individual
packets (`PcapPacket`).
"""

import struct
from datetime import datetime, timedelta
from protocol_enums import DataLinkType, NetworkProtocol, TransportProtocol
from packet_parser import GlobalHeaderParser, link_layer_parsers, network_layer_parsers, transport_layer_parsers 

DEBUG_FILE = 'debug.txt'
ETHERNET_HEADER_SIZE = 14


class PcapPacketFactory:
    """
    Factory class for creating `PcapPacket` objects from a PCAP file. Supports Ethernet packets.
    """
    def __init__(self, file, debug_mode=False):
        """
        Initialize the factory with a PCAP file.

        Args:
            file (file object): Open PCAP file for reading.
            debug_mode (bool): Enables debugging mode if True.
        """
        self.file = file
        self.global_header = None  # Global header of the PCAP file
        self.base_timestamp = None  # Timestamp of the first packet
        self.debug_mode = debug_mode
        self.dll_handlers = {
            DataLinkType.ETHERNET: self.populate_ethernet_packet  # Handler for Ethernet packets
        }

    def parse_global_header(self):
        """
        Parse the global header of the PCAP file.

        Returns:
            dict: Parsed global header metadata.
        """
        header = self.file.read(24)
        self.global_header = GlobalHeaderParser.parse(header)
        return self.global_header

    def __iter__(self):
        """
        Make the factory iterable to yield parsed packets from the PCAP file.

        Yields:
            PcapPacket: Parsed packet object or None for unsupported packet types.
        """
        if not self.global_header:
            self.parse_global_header()

        while True:
            packet_header = self.file.read(16)
            if len(packet_header) < 16:
                break

            header_attributes = struct.unpack(self.global_header["byte_order"] + 'IIII', packet_header)
            ts_sec, ts_usec, incl_len, orig_len = header_attributes

            # Adjust timestamp precision
            if self.global_header["timestamp_precision"] == "microseconds":
                timestamp = datetime.fromtimestamp(ts_sec) + timedelta(microseconds=ts_usec)
            elif self.global_header["timestamp_precision"] == "nanoseconds":
                timestamp = datetime.fromtimestamp(ts_sec) + timedelta(microseconds=ts_usec / 1000)

            if self.base_timestamp is None:
                self.base_timestamp = timestamp

            relative_time = (timestamp - self.base_timestamp).total_seconds()

            packet_data = self.file.read(incl_len)
            if len(packet_data) < incl_len:
                continue

            packet = PcapPacket(header_attributes, timestamp, relative_time)

            dll_type = DataLinkType(self.global_header.get("network"))
            handler = self.dll_handlers.get(dll_type)
            if handler:
                packet = handler(packet, packet_data)
            else:
                print(f"Error: Data Link type '{dll_type}' not supported")
                return None
            yield packet

    def populate_ethernet_packet(self, packet, packet_data):
        """
        Populate Ethernet-specific headers and payloads in the packet.

        Args:
            packet (PcapPacket): Packet object to populate.
            packet_data (bytes): Raw packet data.

        Returns:
            PcapPacket: Packet with populated headers and payload.
        """
        ethernet_parser = link_layer_parsers.get(DataLinkType.ETHERNET.value)
        ethernet_result = ethernet_parser.parse(packet_data)
        packet.data_link_header = ethernet_result.get("metadata")

        network_type_value = packet.data_link_header.get("network_type")
        if network_type_value in NetworkProtocol._value2member_map_:
            network_type = NetworkProtocol(network_type_value)
        else:
            return None

        network_parser = network_layer_parsers.get(network_type.value)
        if network_parser:
            network_result = network_parser.parse(packet_data[ETHERNET_HEADER_SIZE:])
            packet.network_header = network_result.get("metadata")

            transport_type = TransportProtocol(packet.network_header.get("protocol"))
            transport_parser = transport_layer_parsers.get(transport_type.value)
            offset = ETHERNET_HEADER_SIZE + packet.network_header.get("header_size")
            if transport_parser:
                transport_result = transport_parser.parse(packet_data[offset:])
                packet.transport_header = transport_result.get("metadata")
                packet.application_data = transport_result.get("payload")

        return packet

    def populate_wifi_packet(self, packet, packet_data):
        """
        Placeholder for populating Wi-Fi packets. Not implemented.
        """
        pass


class PcapPacket:
    """
    Represents a single packet from a PCAP file, with headers and payload.
    """
    def __init__(self, attributes, timestamp, relative_time):
        """
        Initialize the PcapPacket with raw header attributes and timestamps.

        Args:
            attributes (tuple): Tuple of timestamp, length, and other raw header fields.
            timestamp (datetime): Absolute timestamp of the packet.
            relative_time (float): Relative time (seconds) from the first packet.
        """
        self.ts_sec, self.ts_usec, self.incl_len, self.orig_len = attributes
        self.timestamp = timestamp  # Absolute timestamp
        self.relative_time_s = relative_time  # Relative time in seconds
        self.data_link_header = None
        self.network_header = None
        self.transport_header = None
        self.application_data = None

    def __str__(self):
        """
        Generate a string representation of the PcapPacket object.

        Returns:
            str: Readable summary of the packet's attributes.
        """
        result = [
            f"Timestamp (seconds): {self.ts_sec}",
            f"Timestamp (microseconds): {self.ts_usec}",
            f"Included Length: {self.incl_len}",
            f"Original Length: {self.orig_len}",
            f"Absolute Timestamp: {self.timestamp}",
            f"Relative Timestamp (s): {self.relative_time_s:.6f}",
            f"Data Link Header: {self.data_link_header if self.data_link_header else 'None'}",
            f"Network Header: {self.network_header if self.network_header else 'None'}",
            f"Transport Header: {self.transport_header if self.transport_header else 'None'}",
            f"Application Data: {'Parsed' if self.application_data else 'None'}",
        ]
        return "\n".join(result)
