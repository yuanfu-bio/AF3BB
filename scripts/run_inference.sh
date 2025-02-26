#!/bin/bash

INPUT_DIR=$1
OUTPUT_DIR=$2
JOBS=$3

# Load configuration and necessary modules
source af3.config
module load singularity

# Generate partitions dynamically based on the num of JOBS
PARTITIONS=()
for ((i=1; i<=JOBS; i++)); do
    PARTITIONS+=("P$i")
done

# Create input and output directories dynamically
mkdir -p "$OUTPUT_DIR"

INPUT_DIRS=()
for partition in "${PARTITIONS[@]}"; do
    INPUT_DIRS+=("$INPUT_DIR/$partition")
    
done

# Loop through the arrays and execute tasks
RUN_AF3_SCRIPT="./run_alphafold.py"
for i in "${!INPUT_DIRS[@]}"; do
    srun -n 1 --gres=gpu:1 --cpus-per-task=25 singularity exec \
         --nv \
         --bind "${INPUT_DIRS[$i]}:/root/af_input" \
         --bind "${OUTPUT_DIR}:/root/af_output" \
         --bind "$MODEL_PARAMETERS_DIR:/root/models" \
         --bind "$DATABASE_DIR:/root/public_databases" \
         "$IMAGE_DIR" \
         bash -c "export CUDA_VISIBLE_DEVICES=$i && \
         python $RUN_AF3_SCRIPT \
         --input_dir=/root/af_input/ \
         --model_dir=/root/models \
         --db_dir=/root/public_databases \
         --output_dir=/root/af_output" &
done
# Wait for all tasks to complete
wait
echo "$(date '+%Y-%m-%d %H:%M:%S')"