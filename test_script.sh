#!/usr/bin/env argorator
# Description: A test script for checking program name behavior

# Number of iterations (int) Default: 5
NUM_ITERATIONS=5

echo "Running $NUM_ITERATIONS iterations"
for i in $(seq 1 $NUM_ITERATIONS); do
    echo "Iteration $i"
done