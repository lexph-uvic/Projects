"""Defines Packet, Flow, and Connection classes for managing network packet analysis."""

class Packet:
    """Represents a packet containing headers, timestamps, sequence/ack numbers, and payload."""

    def __init__(self, ethernet_header, ipv4_header, tcp_header, relative_time_s, payload):
        self.ethernet_header = ethernet_header
        self.ipv4_header = ipv4_header
        self.tcp_header = tcp_header
        self.time_s = relative_time_s
        self.payload = payload
        self.seq_number = tcp_header["seq_number"]
        self.ack_number = tcp_header["ack_number"]

    def get_direction(self):
        """Return the packet's direction as a tuple (src_ip, src_port, dest_ip, dest_port)."""
        return (
            self.ipv4_header.get("src_ip"),
            self.tcp_header.get("src_port"),
            self.ipv4_header.get("dest_ip"),
            self.tcp_header.get("dest_port"),
        )

    def get_opposite_direction(self):
        """Return the reverse direction (dest_ip, dest_port, src_ip, src_port)."""
        return (
            self.ipv4_header.get("dest_ip"),
            self.tcp_header.get("dest_port"),
            self.ipv4_header.get("src_ip"),
            self.tcp_header.get("src_port"),
        )


class Flow:
    """A flow representing packets in one direction of a TCP connection."""

    def __init__(self, direction=None):
        self.packets = []
        self.direction = direction  # (src_ip, src_port, dest_ip, dest_port)
        self.total_bytes = 0

    def add_packet(self, packet):
        """Add a packet to the flow and update the total byte count."""
        self.packets.append(packet)
        self.packets.sort(key=lambda p: (p.seq_number, p.time_s))  # Sort by seq number, then timestamp
        self.total_bytes += len(packet.payload)

    def get_packet_count(self):
        """Return the number of packets in the flow."""
        return len(self.packets)


class Connection:
    """Represents a TCP connection consisting of two flows: flow_ab and flow_ba."""

    def __init__(self, packet=None):
        # Define flows for the connection's two directions
        self.flow_ab = Flow(packet.get_direction())            # Flow from A to B
        self.flow_ba = Flow(packet.get_opposite_direction())   # Flow from B to A

        self.start_time = packet.time_s
        self.end_time = packet.time_s
        self.SYN_count = 1 if packet.tcp_header.get("flags").get("syn") else 0
        self.FIN_count = 1 if packet.tcp_header.get("flags").get("fin") else 0
        self.has_rst = bool(packet.tcp_header.get("flags").get("rst"))  # Changed for clarity
        self.is_complete = False    # A connection is incomplete without both SYN and FIN
        self.is_closed = False

        # Add the initial packet to flow_ab
        self.flow_ab.add_packet(packet)

    def add_packet(self, packet):
        """Add a packet to the appropriate flow and update connection state."""
        direction = packet.get_direction()

        if direction == self.flow_ab.direction:
            self.flow_ab.add_packet(packet)
        elif direction == self.flow_ba.direction:
            self.flow_ba.add_packet(packet)
        else:
            raise ValueError("Packet direction does not match any flow in the connection.")

        # Update timing and flag counts
        self.start_time = min(self.start_time, packet.time_s)
        self.end_time = max(self.end_time, packet.time_s)
        self.SYN_count += int(packet.tcp_header.get("flags").get("syn", 0))
        self.FIN_count += int(packet.tcp_header.get("flags").get("fin", 0))
        self.is_complete = self.SYN_count > 0 and self.FIN_count > 0

        if packet.tcp_header.get("flags", {}).get("rst"):
            self.has_rst = True

        # Update connection closure status
        if self.is_closed and packet.payload:
            self.is_closed = False  # Reopen connection if data follows a FIN
        elif packet.tcp_header.get("flags").get("fin"):
            self.is_closed = True  # Mark as closed if FIN is received

    def get_first_packet(self):
        """Return the earliest packet in the connection by timestamp."""
        min_packet_ab = self.flow_ab.packets[0] if self.flow_ab.packets else None
        min_packet_ba = self.flow_ba.packets[0] if self.flow_ba.packets else None

        if min_packet_ab and min_packet_ba:
            return min_packet_ab if min_packet_ab.time_s < min_packet_ba.time_s else min_packet_ba
        return min_packet_ab or min_packet_ba  # Return whichever is present

    def get_packets(self):
        """Return all packets in the connection, combining both flows."""
        return self.flow_ab.packets + self.flow_ba.packets

    @property
    def total_bytes(self):
        """Return the total byte count of the connection."""
        return self.flow_ab.total_bytes + self.flow_ba.total_bytes

    @property
    def duration(self):
        """Return the connection duration as end_time - start_time."""
        return self.end_time - self.start_time

    @property
    def packet_count(self):
        """Return the total packet count of the connection."""
        return self.flow_ab.get_packet_count() + self.flow_ba.get_packet_count()
