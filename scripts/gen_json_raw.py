#! /usr/bin/env python
# 1. Generate raw MSA input json

import pandas as pd
import json
import os
import shutil
import argparse
import re
from typing import List

def gen_MSA_json(name: str, chains: List[str], prefix: str = "") -> dict:
    """
    General MSA generation function, adaptable to multiple chains 
    
    :param name: Name of the protein.
    :param chains: List of protein sequences.
    :param prefix: A single upper letter (A-Z) or empty string, default is empty.
    :return: Dictionary representing the MSA JSON data.
    :raises ValueError: If prefix is not a single letter or empty.
    """

    if not re.fullmatch(r"[A-Z]?", prefix):
        raise ValueError("Prefix must be a single upper letter (A-Z) or empty.")

    modelSeeds = [1]
    sequences = [{"protein": {"id": f"{prefix}{chr(65 + idx)}", "sequence": seq}} for idx, seq in enumerate(chains) if pd.notna(seq)]
    data = {"name": name, "modelSeeds": modelSeeds, "sequences": sequences, "dialect": "alphafold3", "version": 1}
    return data

def read_by_row(raw_json_dir, row, prefix):
    """ Read row data and generate a JSON file """
    name = row["name"].strip()
    
    # Dynamically retrieve all columns starting with "chain" (e.g., chain1, chain2, chain3, ...)
    chain_columns = [col for col in row.index if col.startswith("chain")]
    
    # Extract chain sequences and remove NaN values
    chains = [row[col].strip() for col in chain_columns if pd.notna(row[col])]

    msa_dict = gen_MSA_json(name, chains, prefix)
    json_path = os.path.join(raw_json_dir, f'{name}.json')

    if os.path.exists(json_path):
        print(f"Warning: File {json_path} already exists. Skipping...")
        return None

    with open(json_path, 'w') as file:
        json.dump(msa_dict, file, indent=4)
    
    return None

def main():
    """ Main function to process target and binders data and generate JSON files """

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate MSA JSON files from protein chain data.")
    parser.add_argument("-t", "--target_csv", required=True, help="Path to the target CSV file")
    parser.add_argument("-b","--binders_csv", required=True, help="Path to the binders CSV file")
    parser.add_argument("-o","--output_dir", required=True, help="Directory to store JSON files")
    parser.add_argument("-j","--jobs", type=int, required=True, help="Directory to store JSON files")
    args = parser.parse_args()

    # Load data
    df_t = pd.read_csv(args.target_csv)
    df_b = pd.read_csv(args.binders_csv)
    raw_json_dir = args.output_dir
    jobs = int(args.jobs)

    # Ensure output directory exists
    os.makedirs(raw_json_dir, exist_ok=True)

    # Process target data
    df_t.apply(lambda row: read_by_row(raw_json_dir, row, "T"), axis=1)

    # Process binders data
    df_b.apply(lambda row: read_by_row(raw_json_dir, row, "B"), axis=1)

    # Create directories for parallel MSA processing
    group_dirs = [f"{raw_json_dir}/P{index}" for index in range(1, jobs+1)]
    for path in group_dirs:
        os.makedirs(path, exist_ok=True)

    # Move JSON files into group directories for parallel processing
    target_json_files = []
    binder_json_files = []
    for file in os.listdir(raw_json_dir):
        if os.path.isfile(os.path.join(raw_json_dir, file)):
            if any(file.startswith(name) for name in df_t["name"]):
                target_json_files.append(file)
            else:
                binder_json_files.append(file)

    # Prioritise target in P1
    for file in target_json_files:
        shutil.move(os.path.join(raw_json_dir, file), os.path.join(group_dirs[0], file))

    for index, file in enumerate(binder_json_files):
        target_dir = group_dirs[index % len(group_dirs)]
        shutil.move(os.path.join(raw_json_dir, file), os.path.join(target_dir, file))

if __name__ == "__main__":
    main()