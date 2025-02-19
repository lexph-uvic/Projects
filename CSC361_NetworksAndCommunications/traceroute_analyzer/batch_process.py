#!/usr/bin/python3.8

"""Copilot Generated
This script processes all `.pcap` files in a specified input directory, analyzes them using the
`traceroute_analyzer.py` script, and saves the output to a specified output directory.

Each `.pcap` file is passed as input to the `traceroute_analyzer.py` script, which generates
a corresponding `.txt` file as output. The output files are named based on the input file
names, with the `.pcap` extension replaced by `.txt`.

Usage:
- Place all `.pcap` files to be processed in the `input` directory.
- The script will automatically create an `output` directory (if it doesn't exist)
  and save the results there.

Requirements:
- Python 3.8 or later.
- `traceroute_analyzer.py` must be in the same directory as this script.
- Ensure the `traceroute_analyzer.py` script can handle the input/output file paths correctly.
"""

import os
import subprocess

def process_pcap_files(input_folder, output_folder):
    """
    Processes `.pcap` files in the input folder using `traceroute_analyzer.py` and saves the
    results to the output folder.

    Args:
        input_folder (str): Path to the folder containing `.pcap` files.
        output_folder (str): Path to the folder where the output `.txt` files will be saved.

    Returns:
        None
    """
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith(".pcap"):
            input_filepath = os.path.join(input_folder, filename)
            output_filepath = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
            subprocess.run(["python3.8", "traceroute_analyzer.py", input_filepath, output_filepath])

if __name__ == "__main__":
    process_pcap_files("input", "output")
