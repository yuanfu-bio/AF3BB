#! /bin/bash

# Initialize the local envirenment
SCRIPT_DIR=$(dirname "$(realpath "$0")")
export PATH=${SCRIPT_DIR}:$PATH

wd="../examples"
log_dir="${wd}/00_log"
data_dir="${wd}/01_data"
json_raw_dir="${wd}/02_json_raw"
json_MSA_dir="${wd}/03_json_MSA"
json_merge_dir="${wd}/04_json_merge"
output_dir="${wd}/05_output"
mkdir -p "${log_dir}"

jobs=4
partition=gpu21
num_models=50

gen_json_raw.py \
    -t "${data_dir}/target.csv" \
    -b "${data_dir}/binders.csv" \
    -o "${json_raw_dir}" \
    -j "${jobs}"

sbatch \
    -J "run_MSA" \
    -p "${partition}" \
    -n "${jobs}" \
    -c 25 \
    -o "${log_dir}/run_MSA_%j.log" \
    -e "${log_dir}/run_MSA_%j.log" \
    run_MSA.sh "${json_raw_dir}" "${json_MSA_dir}" "${jobs}"
wait

merge.py \
    -t "${data_dir}/target.csv" \
    -i "${json_MSA_dir}" \
    -o "${json_merge_dir}" \
    -j "${jobs}" \
    -m "${num_models}"

sbatch \
    -J "run_inference" \
    -p "${partition}" \
    -n "${jobs}" \
    -c 25 \
    -o "${log_dir}/run_inference_%j.log" \
    -e "${log_dir}/run_inference_%j.log" \
    --gres=gpu:${jobs} \
    run_inference.sh "${json_merge_dir}" "${output_dir}" "${jobs}"
wait