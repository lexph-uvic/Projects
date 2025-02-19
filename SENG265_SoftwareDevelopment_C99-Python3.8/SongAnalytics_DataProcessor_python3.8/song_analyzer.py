#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 8 14:44:33 2024
Based on: https://www.kaggle.com/datasets/nelgiriyewithana/top-spotify-songs-2023
Sample input: --filter="ARTIST" --value="Dua Lipa" --order_by="STREAMS" --order="ASC" --limit="6"'
@author: rivera
@author: lexph
"""
import sys
from typing import Dict, List, TextIO

import pandas as pd

OUTPUT_FILE = 'output.csv'

def split_valid_str(arg: str) -> List[str]:
    """ [Copilot Generated Docstring in accordance to Pep 8]
    Splits a command-line argument into a key-value pair.

    Parameters
    ----------
    arg : str
        A command-line argument in the format '--key="value"'.

    Returns
    -------
    list
        A list containing the argument key and value.

    Raises
    ------
    SystemExit
        If the argument cannot be split into exactly two parts, or if the key is not known, the function 
        terminates the program with an error message.
    """
    known_keys = ["--data", "--filter", "--value", "--order_by", "--order", "--limit"]
    key_value = arg.split('=')

    if len(key_value) == 2:
        if key_value[0] in known_keys:
            if key_value[1].startswith('"') and key_value[1].endswith('"'):
                key_value[1] = key_value[1][1:-1]
            return key_value
        else:
            sys.exit(f"Error: Unknown key '{key_value[0]}'. Expected keys are {known_keys}.")
    else:
        sys.exit("Error: Invalid argument format. Expected format: 'key=value'.")


def create_args_dict(args: list) -> Dict[str, str]:
    """ [Copilot Generated Docstring in accordance to Pep 8]
    Creates a dictionary from command-line arguments.

    Parameters
    ----------
    args : list
        A list of command-line arguments in the format '--key="value"'.

    Returns
    -------
    Dict[str, str]
        A dictionary where each key-value pair corresponds to an argument.

    Notes
    -----
    This function uses the `split_valid_str` function to split each argument into a key-value pair.
    """
    return {key: value for key, value in (split_valid_str(item) for item in args) if key is not None}


def process_data(df: pd.DataFrame, args: Dict[str, str]) -> pd.DataFrame:
    """ [Copilot Generated Docstring in accordance to Pep 8]
    Processes data based on input arguments.

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame to be processed.
    args : Dict[str, str]
        A dictionary of arguments to determine how the data should be processed.

    Returns
    -------
    pd.DataFrame
        The processed DataFrame.

    Raises
    ------
    SystemExit
        If the '--order_by' or '--order' arguments are not valid, the function terminates the program with an error message.

    Notes
    -----
    This function performs several operations on the DataFrame, including converting date columns, dropping unused columns, 
    filtering rows, sorting the DataFrame, and limiting the number of output rows. The specific operations performed depend 
    on the input arguments.
    """
    
    # Convert released Year, Month, Day columns to a DateTime type column 'released'.
    df['released'] = pd.to_datetime(df['released_year'].astype(str) + '-' + df['released_month'].astype(str) + '-' + df['released_day'].astype(str), format='%Y-%m-%d')

    # Drop unused columns from dataframe
    df = df.drop(['artist_count', 'released_year', 'released_month', 'released_day', 'bpm', 'key', 'mode', 'danceability_%'], inplace=False, axis=1)   
 
    # Optional: Filter dataframe rows by the '--value' given in the '--filter' column.
    if args.get('--filter') is not None and args.get('--value') is not None:
        if args['--filter'] == 'ARTIST':
            df = df.loc[df['artist(s)_name'].str.contains(args.get('--value'))]
        elif args['--filter'] == 'YEAR':
            df = df.loc[df['released'].dt.year == int(args.get('--value'))]
        else:
            print(f"Error: No value assigned to --filter.")
    
    # Mandatory: Sort dataframe by '--order_by' column, then ascending or descending.      
    if args.get('--order_by') is not None and args.get('--order') is not None:
        order_by: str = None
        if args['--order_by'] == 'NO_APPLE_PLAYLISTS':
            order_by = 'in_apple_playlists'
            df.drop(['in_spotify_playlists', 'streams'], inplace=True, axis = 1)     
        elif args['--order_by'] == 'NO_SPOTIFY_PLAYLISTS':
            order_by = 'in_spotify_playlists'
            df.drop(['in_apple_playlists', 'streams'], inplace=True, axis = 1)
        elif args['--order_by'] == 'STREAMS':
            order_by = 'streams'
            df.drop(['in_apple_playlists', 'in_spotify_playlists'], inplace=True, axis = 1)
        else:
            sys.exit(f"Error: Unexpected value for '--order_by': {args['--order_by']}")

        # Sort Ascending/Descending
        is_ascending: bool = True if args.get('--order') == 'ASC' else False
        df = df.sort_values(order_by, ascending=is_ascending)

        # Optional: Limit row output with '--limit' value
        if args.get('--limit') is not None:
            df = df.head(int(args.get('--limit'))) 
  
    else:
        sys.exit(f"Error: --order_by: '{args.get('--order_by')}' Or --order: '{args.get('--order')}' is not valid.")   
        
    return df

def write_to_file(df: pd.DataFrame, cvs_file: TextIO) -> None:
    """ [Copilot Generated Docstring in accordance to Pep 8]
    Writes a DataFrame to a CSV file.

    This function formats the 'released' column from datetime type to string with the format '%a, %B %d, %Y'.
    It then reorders the DataFrame columns, placing 'released', 'track_name', and 'artist(s)_name' first, 
    followed by the remaining columns in their original order. Finally, it writes the DataFrame to a CSV file,
    excluding the index.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to be written to a CSV file.
    cvs_file : TextIO
        The CSV file to which the DataFrame will be written.

    Returns
    -------
    None
    """
    # Format 'released' column form datetime type to string with output format
    df['released'] = df['released'].dt.strftime('%a, %B %d, %Y')

    # Assign output column order, create new dataframe
    base_column_order = ['released', 'track_name', 'artist(s)_name']
    remaining_columns = [col for col in df.columns if col not in base_column_order]
    df = df[base_column_order + remaining_columns]

    # Output dataframe to csv file 'OUTPUT_FILE', without indexing
    df.to_csv(cvs_file, index=False) 


def main():
    """ [Copilot Generated Docstring in accordance to Pep 8]
    Main entry point of the program. It creates an argument dictionary from the command-line arguments,
    reads the data file into a DataFrame, processes the DataFrame based on the inputted arguments, and
    prints the processed DataFrame.

    Raises
    ------
    SystemExit
        If the '--data' key is not found in the command-line arguments, or if the data file cannot be found,
        the function terminates the program with an error message.
    """ 

    # Create argument dictionary
    main_args_dict: Dict[str, str] = create_args_dict(sys.argv[1:])

    # Try to get the data file name
    try:
        data_file = main_args_dict['--data']
    except KeyError:
        sys.exit("Error: Key '--data' not found. Please provide input data file as command-line argument. Expected format: '--data=%%FILENAME%%.csv'")

    # Try to open the data file and read it into a DataFrame
    try:
        with open(data_file, 'r') as file:
            df = pd.read_csv(file)
    except FileNotFoundError:
        sys.exit(f"Error: File '{data_file}' not found.")

    # Process DataFrame based on inputted questions
    df = process_data(df, main_args_dict)
    # print(f"---After Process--\n{df}")

    # Write DataFrame to output file
    with open(OUTPUT_FILE, 'w') as file:
        write_to_file(df, file)
    


if __name__ == '__main__':
    main()
