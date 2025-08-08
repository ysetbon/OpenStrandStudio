import os
import json
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

def analyze_json_files(base_dir):
    # Dictionary to store results with m,n as separate keys for easier plotting
    results = defaultdict(lambda: {'va': [], 'ha': [], 'n': []})
    
    # Get all subdirectories
    subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and '_rh_continuation' in d]
    
    # Track unique m and n values for color mapping
    unique_m = set()
    max_n = 0
    
    for dir_name in subdirs:
        try:
            # Extract m and n from directory name
            parts = dir_name.split('x')
            m = int(parts[0].replace('m', ''))
            n = int(parts[1].split('_')[0].replace('n', ''))
            
            unique_m.add(m)
            max_n = max(max_n, n)
            
            dir_path = os.path.join(base_dir, dir_name)
            
            # Process all files ending with '_extended' in this directory
            for file in os.listdir(dir_path):
                if '_extended' in file:
                    try:
                        parts = file.split('_')
                        va = float([p.replace('va', '') for p in parts if 'va' in p][0])
                        ha = float([p.replace('ha', '') for p in parts if 'ha' in p][0])
                        
                        # Store values under m key
                        results[m]['va'].append(va)
                        results[m]['ha'].append(ha)
                        results[m]['n'].append(n)  # Store n for darkness
                    except Exception as e:
                        print(f"Error parsing file {file}: {e}")
                        
        except Exception as e:
            print(f"Error processing directory {dir_name}: {e}")

    # Create plots directory if it doesn't exist
    plots_dir = os.path.join(base_dir, 'plots')
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
    
    # Create a dictionary to organize data by both m and n
    mn_results = defaultdict(lambda: {'va': [], 'ha': []})
    
    # Reorganize data by both m and n
    for m in results:
        for va, ha, n in zip(results[m]['va'], results[m]['ha'], results[m]['n']):
            mn_key = (m, n)  # tuple of (m,n) as key
            mn_results[mn_key]['va'].append(va)
            mn_results[mn_key]['ha'].append(ha)
    
    # Generate rainbow colors based on total number of unique m,n combinations
    edge_colors = plt.cm.rainbow(np.linspace(0, 1, len(mn_results)))
    
    # Plot points for each m,n combination in separate figures
    for (m, n), edge_color in zip(sorted(mn_results.keys()), edge_colors):
        # Create a new figure for each m,n combination
        plt.figure(figsize=(10, 8))
        
        va_values = mn_results[(m, n)]['va']
        ha_values = mn_results[(m, n)]['ha']
        
        # Create scatter plot
        plt.scatter(ha_values, va_values, 
                   c=[edge_color],
                   alpha=0.5,
                   s=100,
                   edgecolors=edge_color,
                   linewidth=2)
        
        plt.xlabel('HA')
        plt.ylabel('VA')
        plt.title(f'VA vs HA for m={m}, n={n}')
        plt.grid(True, alpha=0.3)
        
        # Set fixed axis limits from 45 to 90
        plt.xlim(45, 90)
        plt.ylim(45, 90)
        
        # Save each plot with a unique filename in the plots directory
        plot_path = os.path.join(plots_dir, f'va_ha_scatter_m{m}_n{n}.png')
        plt.savefig(plot_path)
        plt.close()
    
    # Close any remaining figures to free up memory
    plt.close('all')

# Use the base directory from your original code
base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
analyze_json_files(base_dir)