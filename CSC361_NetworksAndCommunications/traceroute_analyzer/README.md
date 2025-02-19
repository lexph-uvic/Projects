# Traceroute Analyzer - README

## Overview
`traceroute_analyzer.py` is a Python program designed to analyze traceroute data from `.pcap` files. It processes network packets to identify intermediate routers, compute Round Trip Times (RTTs), and handle fragmented datagrams. The program supports the analysis of both Linux (UDP-based) and Windows (ICMP-based) traceroute packets.

## Features
- **Traceroute Analysis**:
  - Identifies intermediate routers along the path to the destination.
  - Computes statistics such as RTT and hop count for each router.
  - Distinguishes between Linux and Windows traceroutes based on protocols.
- **Fragment Handling**:
  - Reassembles fragmented IP datagrams and analyzes the payload.
  - Provides detailed information about fragmentation, including fragment counts and offsets.
- **Output Options**:
  - Prints results to the console or saves them to a file for further analysis.

## Dependencies
- Python 3.8 or higher
- Standard libraries: `os`, `sys`, `struct`, `collections`, `datetime`, `Enum`
- Custom modules:
  - `protocol_enums.py` (for enumerations of network protocols)
  - `pcap_packet_factory.py` (for parsing pcap files and generating packets)
  - `packet_parser.py` (contains protocol parsers)
  - `traceroute.py` (for managing probes, answers, and fragmented datagrams)

## Usage
### Setup
1. Ensure the following program files are in the same directory:
   - `traceroute_analyzer.py` (main module)
   - `protocol_enums.py` (for protocol definitions)
   - `pcap_packet_factory.py` (for handling `.pcap` files)
   - `packet_parser.py` (for `.pcap` packet parsing)
   - `traceroute.py` (for traceroute data models)
   - `batch_process.py` [optional] (batch input file processing) 

2. Ensure the main script is executable:
```bash
chmod +x traceroute_analyzer.py
```

3. Run the script:
```bash
./traceroute_analyzer.py <filename.pcap> [outputfile]
```
   Replace <filename.pcap> with the path to your pcap file.

### Example Usage:
```bash 
./traceroute_analyzer.py sample.pcap results.txt   # print to file
./traceroute_analyzer.py sample.pcap               # print to console
```

### Batch Processing 
To process multiple **.pcap** files in a ***input*** subdirectory and write the results to corresponding output files
within a ***output*** subdirectory, run the script:
```bash 
./batch_process.py
```
**Ensure that `batch_process.py` has execution privileges and all intended input `.pcap` files are within the ***input*** subdirectory.

## Modules:
- `traceroute_analyzer.py`: Main script for traceroute analysis and output generation.
- `protocol_enums.py`: Enumerations for DataLink, Network, Transport, and ICMP protocols.
- `pcap_packet_factory.py`: Parses pcap files and generates structured packet objects.
- `packet_parser.py`: Handles the parsing of low-level packet headers across data link, network, and transport layers.
- `traceroute.py`: Contains models for probes, answers, fragmented datagrams, and traceroute processing.

## Author
Lex Phillips

## Acknowledgments
Portions of this README file structure was generated using Microsoft Copilot and subsequently reviewed by the author. 