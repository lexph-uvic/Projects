from protocol_enums import TransportProtocol, ICMPType, NetworkProtocol
from packet_parser import network_layer_parsers, transport_layer_parsers

class Probe:
    """
    Represents a network probe packet, which can be either a probe or its response.

    Attributes:
        is_probe (bool): Indicates if the object represents a probe (True) or an answer (False).
        relative_time_s (float): Relative timestamp of the packet in seconds.
        src_ip (str): Source IP address of the packet.
        dest_ip (str): Destination IP address of the packet.
        ttl (int): Time-to-live (TTL) value from the packet header.
        src_port (int): Source port (for UDP probes).
        dest_port (int): Destination port (for UDP probes).
        identifier (int): ICMP identifier (for ICMP probes).
        sequence_number (int): ICMP sequence number (for ICMP probes).
        key (tuple): Unique key to associate the probe with its response.
        os (str): Operating system associated with the probe ("Linux", "Windows", or "Unknown").
    """

    def __init__(self, is_probe, relative_time_s, src_ip, dest_ip,
                 ttl=-1, src_port=None, dest_port=None, identifier=None,
                 sequence_number=None, key=None, os=None):
        """
        Initializes a Probe object with packet metadata.

        Args:
            is_probe (bool): True if the object represents a probe, False otherwise.
            relative_time_s (float): Relative timestamp of the packet.
            src_ip (str): Source IP address.
            dest_ip (str): Destination IP address.
            ttl (int): Time-to-live (TTL) value.
            src_port (int): Source port for UDP packets.
            dest_port (int): Destination port for UDP packets.
            identifier (int): ICMP identifier.
            sequence_number (int): ICMP sequence number.
            key (tuple): Unique key for probe-response association.
            os (str): Operating system inferred from the packet ("Linux", "Windows", or "Unknown").
        """
        self.is_probe = is_probe
        self.relative_time_s = relative_time_s
        self.src_ip = src_ip
        self.dest_ip = dest_ip
        self.ttl = ttl
        self.src_port = src_port
        self.dest_port = dest_port
        self.identifier = identifier
        self.sequence_number = sequence_number
        self.key = key
        self.os = os or "Unknown"

    def __str__(self):
        """
        Returns a string representation of the Probe object.

        Returns:
            str: A formatted string summarizing the probe or answer attributes.
        """
        probe_type = "Probe" if self.is_probe else "Answer"
        return (
            f"{probe_type}:\n"
            f"  Relative Time (s): {self.relative_time_s}\n"
            f"  Source IP: {self.src_ip}\n"
            f"  Destination IP: {self.dest_ip}\n"
            f"  TTL: {self.ttl}\n"
            f"  Source Port: {self.src_port}\n"
            f"  Destination Port: {self.dest_port}\n"
            f"  Identifier: {self.identifier}\n"
            f"  Sequence Number: {self.sequence_number}\n"
            f"  Key: {self.key}\n"
            f"  OS: {self.os}"
        )

    @staticmethod
    def from_packet(packet, is_probe):
        """
        Creates a Probe object from a packet.

        Args:
            packet: Parsed network packet object.
            is_probe (bool): True if the packet represents a probe, False otherwise.

        Returns:
            Probe: A new Probe object based on the packet's attributes.

        Raises:
            ValueError: If the packet protocol is unsupported.
        """
        relative_time_s = packet.relative_time_s
        src_ip = packet.network_header.get("src_ip")
        dest_ip = packet.network_header.get("dest_ip")
        ttl = packet.network_header.get("ttl") if is_probe else -1
        key = Probe.generate_key(packet, is_probe)
        os = "Unknown"
        identifier = None
        sequence_number = None

        if packet.transport_header and packet.network_header.get("protocol") == TransportProtocol.UDP.value:
            src_port = packet.transport_header.get("src_port")
            dest_port = packet.transport_header.get("dest_port")
            os = "Linux"
            return Probe(is_probe, relative_time_s, src_ip, dest_ip, ttl, src_port, dest_port, key=key, os=os)
        elif packet.transport_header and packet.network_header.get("protocol") == TransportProtocol.ICMP.value:
            if packet.transport_header.get("icmp_type") in {ICMPType.REPLY.value, ICMPType.REQUEST.value}:
                identifier = packet.transport_header.get("identifier")
                sequence_number = packet.transport_header.get("sequence_number")
                os = "Windows"
            elif packet.transport_header.get("icmp_type") in {ICMPType.UNREACHABLE.value, ICMPType.EXCEEDED.value}:
                network_header, transport_header = Probe._get_embedded_headers(packet)
                protocol_value = network_header.get("protocol") if network_header else None
                if protocol_value == TransportProtocol.UDP.value:
                    os = "Linux"
                elif protocol_value == TransportProtocol.ICMP.value:
                    os = "Windows"
            return Probe(is_probe, relative_time_s, src_ip, dest_ip, ttl,
                         identifier=identifier, sequence_number=sequence_number, os=os, key=key)
        raise ValueError("Unsupported protocol for creating a Probe.")

    @staticmethod
    def _get_embedded_headers(packet):
        """
        Extracts embedded headers from an ICMP payload.

        Args:
            packet: Packet containing an embedded IP header and beyond.

        Returns:
            tuple: (network_header, transport_header) or (None, None) if extraction fails.
        """
        embedded_data = packet.application_data
        network_type_value = packet.data_link_header.get("network_type")
        if network_type_value in NetworkProtocol._value2member_map_:
            network_type = NetworkProtocol(network_type_value)
        else:
            return None, None
        network_parser = network_layer_parsers.get(network_type.value)
        if network_parser:
            network_result = network_parser.parse(embedded_data)
            network_header = network_result.get("metadata")
            transport_type = TransportProtocol(network_header.get("protocol"))
            transport_parser = transport_layer_parsers.get(transport_type.value)
            offset = network_header.get("header_size")
            if transport_parser:
                transport_result = transport_parser.parse(embedded_data[offset:])
                transport_header = transport_result.get("metadata")
                return network_header, transport_header
        return None, None

    @staticmethod
    def is_probe(packet):
        """
        Determines if a packet is a probe.

        Args:
            packet: Parsed network packet.

        Returns:
            bool: True if the packet is a probe, False otherwise.
        """
        if packet.network_header:
            if packet.transport_header and packet.network_header.get("protocol") == TransportProtocol.UDP.value:
                return 33434 <= packet.transport_header.get("dest_port", 0) <= 33529
            elif packet.transport_header and packet.network_header.get("protocol") == TransportProtocol.ICMP.value:
                return packet.transport_header.get("icmp_type", 0) == ICMPType.REQUEST.value
        return False

    @staticmethod
    def is_answer(packet):
        """
        Determines if a packet is an answer to a probe.

        Args:
            packet: Parsed network packet.

        Returns:
            bool: True if the packet is an answer, False otherwise.
        """
        if packet.network_header and packet.network_header.get("protocol") == TransportProtocol.ICMP.value:
            return packet.transport_header.get("icmp_type", -1) in {
                ICMPType.UNREACHABLE.value,
                ICMPType.EXCEEDED.value,
            }
        return False

    @staticmethod
    def is_fragmented(packet):
        """
        Determines if a packet is fragmented.

        Args:
            packet: Parsed network packet.

        Returns:
            bool: True if the packet is fragmented, False otherwise.
        """
        if not packet.network_header:
            raise ValueError("'is_fragmented()' failed: packet.network_header is None")
        flags = packet.network_header.get("flags", {})
        return flags.get("mf", 0) or packet.network_header.get("fragment_offset", 0) != 0

    @staticmethod
    def generate_key(packet, is_probe):
        """
        Generates a unique key for a probe or its answer.

        Args:
            packet: Parsed network packet.
            is_probe (bool): True if the packet is a probe, False otherwise.

        Returns:
            tuple: Unique key for the packet.
        """
        try:
            if is_probe:
                if packet.network_header["protocol"] == TransportProtocol.UDP.value:
                    return (packet.network_header["src_ip"], packet.network_header["dest_ip"], packet.transport_header["dest_port"], None)
                elif packet.network_header["protocol"] == TransportProtocol.ICMP.value:
                    return (packet.network_header["src_ip"], packet.network_header["dest_ip"], None, packet.transport_header["sequence_number"])
            else:
                embedded_data = packet.application_data
                network_parser = network_layer_parsers[packet.data_link_header["network_type"]]
                embedded_network_header = network_parser.parse(embedded_data)["metadata"]
                offset = embedded_network_header["header_size"]
                transport_parser = transport_layer_parsers[embedded_network_header["protocol"]]
                embedded_transport_header = transport_parser.parse(embedded_data[offset:])["metadata"]
                if embedded_network_header["protocol"] == TransportProtocol.UDP.value:
                    return (embedded_network_header["src_ip"], embedded_network_header["dest_ip"], embedded_transport_header["dest_port"], None)
                elif embedded_network_header["protocol"] == TransportProtocol.ICMP.value:
                    return (embedded_network_header["src_ip"], embedded_network_header["dest_ip"], None, embedded_transport_header["sequence_number"])
        except KeyError:
            return None
        except (TypeError, IndexError):
            return None



class ProbeAnswer:
    """
    Represents a probe and its corresponding answer.

    Attributes:
        probe (Probe): The probe associated with this object.
        answer (Probe): The answer associated with the probe, if available.
        is_complete (bool): Indicates whether the probe-answer pair is complete.
        rtt (float): Round-trip time (RTT) in seconds.
        hop (int): The hop count derived from the probe's TTL.
        router_ip (str): The IP address of the router responding to the probe.
        completion_time_s (float): Time at which the answer was received, in seconds.
    """

    def __init__(self, probe):
        """
        Initializes a ProbeAnswer object.

        Args:
            probe (Probe): The initial probe for the pair.
        """
        self.probe = probe
        self.answer = None
        self.is_complete = False
        self.rtt = 0
        self.hop = 0
        self.router_ip = None
        self.completion_time_s = 0

    def add_answer(self, answer):
        """
        Adds an answer to the probe and marks the pair as complete.

        Args:
            answer (Probe): The answer to the associated probe.

        Raises:
            ValueError: If the operating system (OS) of the probe and answer do not match.
        """
        if self.probe.os != answer.os:
            raise ValueError(f"Mis-matching probe-answer operating system types. Probe: {self.probe.os}, Answer: {answer.os}")
        self.answer = answer
        self.is_complete = True
        self.completion_time_s = answer.relative_time_s
        self._populate_probe_attributes()

    def _populate_probe_attributes(self):
        """
        Populates RTT, hop count, and router IP based on the probe and answer.
        """
        self.rtt = self.answer.relative_time_s - self.probe.relative_time_s
        self.hop = self.probe.ttl
        self.router_ip = self.answer.src_ip

    def __str__(self):
        """
        Returns a string representation of the ProbeAnswer object.

        Returns:
            str: A formatted string summarizing the probe-answer pair.
        """
        result = [
            f"Operating system: {self.probe.os}",
            f"Source IP: {self.probe.src_ip}",
            f"Destination IP: {self.probe.dest_ip}",
            f"Router IP: {self.router_ip if self.is_complete else 'Incomplete'}",
            f"Hop: {self.hop if self.is_complete else 'Unknown'}",
            f"RTT: {self.rtt:.6f} seconds" if self.is_complete else "RTT: Incomplete",
            f"Received: {self.completion_time_s:.6f} seconds" if self.is_complete else "Incomplete",
        ]
        return "\n".join(result)



class FragmentedDatagram:
    """
    Handles reassembly of fragmented IP datagrams from individual fragments.

    Attributes:
        count (int): Tracks the number of FragmentedDatagram instances.
        is_complete (bool): Indicates whether the datagram is fully reassembled.
        received_payload (int): Total payload size received so far.
        total_payload (int): Expected total payload size for the datagram.
        timestamps (list): List of timestamps (relative time) for received fragments.
        fragments (list): List of individual packet fragments.
        last_offset (int): Offset of the last fragment in the datagram.
    """
    count = 0

    def __init__(self, packet):
        """
        Initializes the FragmentedDatagram instance and processes the first fragment.

        Args:
            packet: The first packet fragment of the datagram.
        """
        self.is_complete = False
        self.received_payload = 0
        self.total_payload = 0
        self.timestamps = []  # Store timestamps (relative_time_s) for fragments
        self.fragments = []
        self.add_fragment(packet)
        self.last_offset = 0
        FragmentedDatagram.count += 1

    def add_fragment(self, packet):
        """
        Adds a fragment to the datagram and checks for reassembly completion.

        Args:
            packet: A packet fragment to add to the datagram.

        Returns:
            Probe: A fully reassembled Probe object if the datagram is complete, else None.
        """
        # Extract payload length and fragment offset
        header_size = packet.network_header.get("ihl") * 4
        total_length = packet.network_header.get("total_length")
        payload_length = total_length - header_size
        fragment_offset = packet.network_header.get("fragment_offset") * 8  # Convert to bytes

        # Ensure fragment starts at the correct offset
        if fragment_offset != self.received_payload:
            print(f"Fragment offset mismatch! Expected: {self.received_payload}, Got: {fragment_offset}")
            return None

        self.received_payload += payload_length
        self.timestamps.append(packet.relative_time_s)  # Track timestamp

        # Add the fragment
        self.fragments.append(packet)

        # Check if this is the last fragment
        if not packet.network_header.get("flags", {}).get("mf", False):
            self.total_payload = fragment_offset + payload_length
            self.last_offset = fragment_offset

        # Check for completion
        if self.total_payload == self.received_payload:
            self.is_complete = True
            avg_timestamp = sum(self.timestamps) / len(self.timestamps)
            first_fragment = self.fragments[0]

            # Construct a Probe from the reassembled datagram
            key = Probe.generate_key(first_fragment, is_probe=True)
            probe = Probe(
                is_probe=True,
                relative_time_s=avg_timestamp,
                src_ip=first_fragment.network_header.get("src_ip"),
                dest_ip=first_fragment.network_header.get("dest_ip"),
                ttl=first_fragment.network_header.get("ttl"),
                src_port=first_fragment.transport_header.get("src_port"),
                dest_port=first_fragment.transport_header.get("dest_port"),
                os="Linux"
            )
            probe.key = key
            return probe

        return None

    @staticmethod
    def generate_key(packet):
        """
        Generates a unique key for identifying a fragmented datagram.

        Args:
            packet: A packet fragment containing the datagram details.

        Returns:
            tuple: A tuple (src_ip, dest_ip, identification) as the unique key.
        """
        if packet.network_header:
            src_ip = packet.network_header.get("src_ip")
            dest_ip = packet.network_header.get("dest_ip")
            indentification = packet.network_header.get("identification")
            return (src_ip, dest_ip, indentification)
        return None
    


class TraceRoute:
    """
    Analyzes traceroute data and computes routing statistics.

    Attributes:
        src_ip (str): Source IP address of the traceroute.
        dest_ip (str): Destination IP address of the traceroute.
        intermediates (list): List of intermediate routers with hop, router IP, and RTT data.
        statistics (list): Computed RTT statistics for each unique router.
    """

    def __init__(self, probes):
        """
        Initializes the TraceRoute instance by processing probes and computing statistics.

        Args:
            probes (dict): Dictionary of probe keys mapped to their corresponding ProbeAnswer objects.
        """
        self.src_ip = None
        self.dest_ip = None
        self.intermediates = []  # List to store intermediates with hop, router_ip, avg_rtt
        self.statistics = []  # Final statistics container

        # Process the probes dictionary to populate the TraceRoute attributes
        self._process_probes(probes)

        # Compute statistics after processing probes
        self._compute_statistics()

    def _process_probes(self, probes):
        """
        Processes probes to populate the intermediates list.

        Args:
            probes (dict): Dictionary of probe keys mapped to their corresponding ProbeAnswer objects.
        """
        # Temporary dictionary to collect data for each router
        router_data = {}

        for probe_answer in probes.values():
            if not probe_answer.is_complete:
                continue  # Skip incomplete probes

            # Set source and destination IP if not already set
            if self.src_ip is None:
                self.src_ip = probe_answer.probe.src_ip
            if self.dest_ip is None:
                self.dest_ip = probe_answer.probe.dest_ip

            # Key by router IP and hop number
            key = (probe_answer.router_ip, probe_answer.hop)
            if key not in router_data:
                router_data[key] = {
                    "router_ip": probe_answer.router_ip,
                    "hop": probe_answer.hop,
                    "rtts": [],  # Collect all RTTs for each router
                    "completion_times": [],
                }

            # Add RTT and completion time
            router_data[key]["rtts"].append(probe_answer.rtt)
            router_data[key]["completion_times"].append(probe_answer.completion_time_s)

        # Populate `intermediates` list
        for data in router_data.values():
            avg_rtt = sum(data["rtts"]) / len(data["rtts"])
            earliest_completion = min(data["completion_times"])
            self.intermediates.append({
                "router_ip": data["router_ip"],
                "hop": data["hop"],
                "avg_rtt": avg_rtt,  # Precomputed average RTT
                "rtts": data["rtts"],  # Store all RTTs for statistics
                "completion_time_s": earliest_completion,
            })

        # Sort intermediates by hop and completion time
        self.intermediates.sort(key=lambda x: (x["hop"], x["completion_time_s"]))

    def _compute_statistics(self):
        """
        Computes RTT statistics for each unique router IP (averages over multiple RTTs per IP).
        """
        unique_router_stats = {}

        # Aggregate all RTTs by unique router IP
        for intermediate in self.intermediates:
            router_ip = intermediate["router_ip"]
            if router_ip not in unique_router_stats:
                unique_router_stats[router_ip] = []
            unique_router_stats[router_ip].extend(intermediate["rtts"])  # Collect all RTTs

        # Compute average RTT and standard deviation for each unique router IP
        for router_ip, rtts in unique_router_stats.items():
            avg_rtt = sum(rtts) / len(rtts)
            std_dev_rtt = (
                (sum((rtt - avg_rtt) ** 2 for rtt in rtts) / len(rtts)) ** 0.5
                if len(rtts) > 1 else 0
            )
            self.statistics.append({
                "router_ip": router_ip,
                "avg_rtt": avg_rtt * 1000,  # Convert to ms
                "std_dev": std_dev_rtt * 1000,  # Convert to ms
            })

    def __str__(self):
        """
        Returns a string representation of the TraceRoute object.

        Returns:
            str: Detailed information about the traceroute, including source/destination IPs,
            intermediate routers, and RTT statistics.
        """
        result = []
        result.append(f"The IP address of the source node: {self.src_ip}")
        result.append(f"The IP address of ultimate destination node: {self.dest_ip}")
        result.append(f"The IP addresses of the intermediate destination nodes:")

        for count, intermediate in enumerate(self.intermediates):
            router_label = "destination" if intermediate["router_ip"] == self.dest_ip else f"router {count + 1}"
            result.append(
                f"  {router_label:<12}: {intermediate['router_ip']:<16} "
                f"Hop:{intermediate['hop']:<4} Avg RTT:{intermediate['avg_rtt']:.2f} ms"
            )

        result.append("\nRTT Statistics:")
        for stat in self.statistics:
            result.append(
                f"The avg RTT between {self.src_ip} and {stat['router_ip']} is: "
                f"{stat['avg_rtt']:.2f} ms, the s.d. is: {stat['std_dev']:.2f} ms"
            )

        return "\n".join(result)