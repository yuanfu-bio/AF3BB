#! /usr/bin/env python

import os
import json
from tqdm import tqdm
import copy
import shutil
import argparse
import pandas as pd


def main():
    """ Main function to merge JSON files of target and binders """

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate MSA JSON files from protein chain data.")
    parser.add_argument("-t", "--target_csv", required=True, help="Path to the target CSV file")
    parser.add_argument("-i", "--input_dir", required=True, help="Directory to store JSON files after MSA")
    parser.add_argument("-o", "--output_dir", required=True, help="Directory to store JSON files after merging")
    parser.add_argument("-j", "--jobs", type=int, required=True, help="Directory to store JSON files")
    parser.add_argument("-m", "--models", type=int, required=True, help="The num of random seeds.")
    args = parser.parse_args()

    df_t = pd.read_csv(args.target_csv)
    input_dir = args.input_dir
    output_dir = args.output_dir
    jobs = int(args.jobs)
    models = args.models

    os.makedirs(output_dir, exist_ok=True)

    target_name = df_t["name"][0]

    shutil.move(f"{input_dir}/P1/{target_name}", f"{input_dir}/{target_name}")

    with open(f"{input_dir}/{target_name}/{target_name}_data.json", 'r') as file:
        target = json.load(file)

    for index in tqdm(range(1, jobs+1)):
        os.makedirs(f"{output_dir}/P{index}", exist_ok=True)

        for binder in tqdm(os.listdir(f"{input_dir}/P{index}")):
            with open(f"{input_dir}/P{index}/{binder}/{binder}_data.json", 'r') as file:
                binder_json = json.load(file)

            complex_json = copy.deepcopy(target)
            complex_json["name"] = f"{target_name}_{binder}"
            complex_json["modelSeeds"] = [i for i in range(1, models+1)] # Specify the number of prediction models
            binder_MSA = binder_json["sequences"]
            complex_json["sequences"].extend(binder_MSA) # Append MSA information of binders

            with open(f'{output_dir}/P{index}/{target_name}_{binder}.json', 'w') as file:
                json.dump(complex_json, file, indent=4)

if __name__ == "__main__":
    main()