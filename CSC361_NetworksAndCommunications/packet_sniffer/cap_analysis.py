"""Module for analyzing TCP connections and calculating connection statistics."""

from statistics import mean


class AnalyzeConnections:
    """Analyze TCP connections and compute statistics on durations, RTTs, and packet/window sizes."""

    def __init__(self, connections):
        self.connections = connections
        self.complete_connections = 0
        self.reset_connections = 0
        self.open_connections_before = 0
        self.open_connections_after = 0
        self.complete_rtts = []
        self.complete_durations = []
        self.complete_connection_packet_counts = []
        self.complete_connection_window_sizes = []

        self.analyze()

    def analyze(self):
        """Analyze all connections and gather relevant statistics."""
        for conn in self.connections.values():
            # Check if the connection is complete
            if conn.is_complete:
                self.complete_connections += 1
                self.complete_durations.append(conn.duration)
                self.complete_rtts.extend(self.calculate_rtt(conn))
                self.complete_connection_packet_counts.append(conn.packet_count)
                self.complete_connection_window_sizes.extend(self.get_window_sizes(conn.get_packets()))

            # Track connections with reset flag
            if conn.has_rst:
                self.reset_connections += 1

            # Track connections established before capture start
            if conn.SYN_count == 0:
                self.open_connections_before += 1

            # Track connections still open after capture end
            if not conn.is_closed:
                self.open_connections_after += 1

    @staticmethod
    def calculate_rtt(connection):
        """Calculate and return a list of Round-Trip Times (RTTs) for the given connection."""
        rtts = []
        flow_ba_iter = iter(connection.flow_ba.packets)  # Iterator for flow_ba packets
        p2 = next(flow_ba_iter, None)  # First packet in flow_ba

        for p1 in connection.flow_ab.packets:
            while p2 and p2.ack_number < p1.seq_number + len(p1.payload):
                p2 = next(flow_ba_iter, None)  # Advance in flow_ba if ack is too low

            if p2 and p2.ack_number >= p1.seq_number + len(p1.payload):
                rtt = p2.time_s - p1.time_s
                if rtt >= 0:
                    rtts.append(rtt)
                break  # Break after finding the first valid ACK

        return rtts

    @staticmethod
    def get_window_sizes(packets):
        """Return a list of TCP window sizes from the given packets."""
        return [packet.tcp_header.get("window_size") for packet in packets]

    # Properties for statistics calculations
    @property
    def min_duration(self):
        """Return the minimum connection duration."""
        return min(self.complete_durations, default=None)

    @property
    def mean_duration(self):
        """Return the mean connection duration."""
        return mean(self.complete_durations) if self.complete_durations else None

    @property
    def max_duration(self):
        """Return the maximum connection duration."""
        return max(self.complete_durations, default=None)

    @property
    def min_rtt(self):
        """Return the minimum RTT."""
        return min(self.complete_rtts, default=None)

    @property
    def mean_rtt(self):
        """Return the mean RTT."""
        return mean(self.complete_rtts) if self.complete_rtts else None

    @property
    def max_rtt(self):
        """Return the maximum RTT."""
        return max(self.complete_rtts, default=None)

    @property
    def min_packet_count(self):
        """Return the minimum packet count."""
        return min(self.complete_connection_packet_counts, default=None)

    @property
    def mean_packet_count(self):
        """Return the mean packet count."""
        return mean(self.complete_connection_packet_counts) if self.complete_connection_packet_counts else None

    @property
    def max_packet_count(self):
        """Return the maximum packet count."""
        return max(self.complete_connection_packet_counts, default=None)

    @property
    def min_window_size(self):
        """Return the minimum TCP window size."""
        return min(self.complete_connection_window_sizes, default=None)

    @property
    def mean_window_size(self):
        """Return the mean TCP window size."""
        return mean(self.complete_connection_window_sizes) if self.complete_connection_window_sizes else None

    @property
    def max_window_size(self):
        """Return the maximum TCP window size."""
        return max(self.complete_connection_window_sizes, default=None)
