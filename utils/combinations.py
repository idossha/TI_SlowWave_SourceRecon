#! /usr/bin/env python3

'''
Script that takes
1. Number of electrodes per list
2. Generates all possible combinations of electrode montages

To be used later for general TI optimization.

Ido Haber
May 2024
'''

import argparse
from itertools import product

def generate_combinations(E1_plus, E1_minus, E2_plus, E2_minus):
    combinations = []
    for e1p, e1m in product(E1_plus, E1_minus):
        for e2p, e2m in product(E2_plus, E2_minus):
            combinations.append(((e1p, e1m), (e2p, e2m)))
    return combinations

def create_electrode_list(prefix, num):
    return [f'{prefix}{i}' for i in range(num)]

def main():
    parser = argparse.ArgumentParser(description='Generate all possible combinations of electrode montages.')
    parser.add_argument('num_electrodes', type=int, help='Number of electrodes per list')

    args = parser.parse_args()

    num_electrodes = args.num_electrodes

    E1_plus = create_electrode_list('E1+', num_electrodes)
    E1_minus = create_electrode_list('E1-', num_electrodes)
    E2_plus = create_electrode_list('E2+', num_electrodes)
    E2_minus = create_electrode_list('E2-', num_electrodes)

    # Generate all combinations
    all_combinations = generate_combinations(E1_plus, E1_minus, E2_plus, E2_minus)

    # Print combinations
    for combo in all_combinations:
        print(combo)

    # Print the number of combinations
    print(f'Total number of combinations: {len(all_combinations)}')

if __name__ == '__main__':
    main()
