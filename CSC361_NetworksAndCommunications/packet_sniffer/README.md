# Packet Sniffer - README

## Overview
`packet_sniffer.py` is a Python program designed to parse and analyze network packets from pcap files. It extracts details at multiple network layers (Ethernet, IPv4, TCP) and provides statistics on TCP connections, including duration, RTT (Round Trip Time), and packet counts.

## Features
- **PCAP Parsing**: Reads and parses `.pcap` files, extracting essential packet data from Ethernet, IPv4, and TCP layers.
- **Connection Analysis**: Tracks and summarizes TCP connections with details like:
  - Connection duration (start and end times)
  - Round Trip Times (RTTs) for each connection
  - Packet and data byte counts for each direction
  - Open/closed status and connection reset count
- **Statistics Summary**: Provides summaries of complete TCP connections, including:
  - Minimum, mean, and maximum connection durations
  - Minimum, mean, and maximum RTTs
  - Minimum, mean, and maximum packet counts
  - Minimum, mean, and maximum TCP window sizes

## Dependencies
- Python 3.8 or higher
- Standard libraries: `struct`, `datetime`, `statistics`, and others as used in custom modules

## Usage
1. Ensure that all program files are in the same directory:
   - `packet_sniffer.py` (main module)
   - `packet_parser.py` (for packet parsing)
   - `connection.py` (for managing TCP connections)
   - `cap_analysis.py` (for analyzing connection statistics)

2. Ensure main script is set as executable:
   - Within linux.csc.uvic.ca server, set executable permission
```bash
chmod +x packet_sniffer.py
```

3. Run the script:
```bash
./packet_sniffer.py <filename.pcap>
```
   Replace <filename.pcap> with the path to your pcap file.

### Example Usage:
```bash 
./packet_sniffer.py sample-capture-file.cap
```

## Modules:
- packet_sniffer.py: Main script to initialize parsing and manage packet flow.
- packet_parser.py: Handles the parsing of packet headers at different network layers.
- connection.py: Manages TCP connection tracking, including sequence numbers and - packet flow.
- cap_analysis.py: Analyzes and summarizes connection statistics, providing detailed insights.

## Author
Lex Phillips

## Acknowledgments
Portions of this README file structure was generated using Microsoft Copilot and subsequently reviewed by the author. 