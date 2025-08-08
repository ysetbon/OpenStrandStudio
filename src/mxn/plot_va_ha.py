import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def extract_va_ha_from_filename(filename):
    """Extract va, ha, and difference values from the filename."""
    va_match = re.search(r'va(\d+)', filename)
    ha_match = re.search(r'ha(\d+)', filename)
    diff1_v_match = re.search(r'diff1_v_([\d.]+)', filename)
    diff2_v_match = re.search(r'diff2_v_([\d.]+)', filename)
    diff1_h_match = re.search(r'diff1_h_([\d.]+)', filename)
    diff2_h_match = re.search(r'diff2_h_([\d.]+)', filename)
    
    if all([va_match, ha_match, diff1_v_match, diff2_v_match, diff1_h_match, diff2_h_match]):
        try:
            # Clean up float values by removing any trailing dots
            return {
                'va': int(va_match.group(1)),
                'ha': int(ha_match.group(1)),
                'diff1_v': float(diff1_v_match.group(1).rstrip('.')),
                'diff2_v': float(diff2_v_match.group(1).rstrip('.')),
                'diff1_h': float(diff1_h_match.group(1).rstrip('.')),
                'diff2_h': float(diff2_h_match.group(1).rstrip('.'))
            }
        except (ValueError, AttributeError) as e:
            print(f"Warning: Skipping malformed filename: {filename}")
            print(f"Error: {e}")
            return None
    return None

def calculate_differences(row):
    """Calculate both difference metrics separately."""
    diff1_delta = abs(row['diff1_h'] - row['diff1_v'])
    diff2_delta = abs(row['diff2_h'] - row['diff2_v'])
    return diff1_delta, diff2_delta

def collect_va_ha_from_directory(base_dir):
    data_list = []
    print("Scanning directory...")
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                values = extract_va_ha_from_filename(file)
                if values:
                    data_list.append(values)

    print(f"Found {len(data_list)} valid files")
    
    if not data_list:
        print("No valid files found with required values")
        return None

    df = pd.DataFrame(data_list)
    df['diff1_delta'] = df.apply(lambda row: abs(row['diff1_h'] - row['diff1_v']), axis=1)
    df['diff2_delta'] = df.apply(lambda row: abs(row['diff2_h'] - row['diff2_v']), axis=1)
    return df

def plot_va_vs_ha(df):
    # Calculate differences
    df['diff1_delta'] = df.apply(lambda row: abs(row['diff1_h'] - row['diff1_v']), axis=1)
    df['diff2_delta'] = df.apply(lambda row: abs(row['diff2_h'] - row['diff2_v']), axis=1)
    
    # Function to create 3D plot
    def create_3d_plot(difference_col, title, zlabel):
        fig = plt.figure(figsize=(15, 12))
        ax = fig.add_subplot(111, projection='3d')
        
        # Filter points with difference < 1
        df_filtered = df[df[difference_col] < 1.0]
        
        # Create scatter plot for main points with high transparency
        scatter = ax.scatter(df_filtered['va'], df_filtered['ha'], df_filtered[difference_col],
                        c=df_filtered[difference_col],
                        cmap='Greens_r',
                        s=100,
                        alpha=0.3)  # More transparent green points
        
        # Add colorbar
        cbar = plt.colorbar(scatter)
        cbar.set_label(zlabel + '\n(showing only differences < 1)', labelpad=15, fontsize=12)
        
        # Get minimum and top 10 minimum points
        sorted_points = df_filtered.sort_values(difference_col)
        min_point = sorted_points.iloc[0]
        top_10_min_points = sorted_points.iloc[1:11]  # Next 10 after minimum
        
        # Get maximum point from filtered data
        max_point = sorted_points.iloc[-1]
        
        # Plot top 10 minimum points with color gradient
        reds = plt.cm.Reds(np.linspace(0.3, 0.7, 10))  # Light to darker red gradient
        for idx, (_, point) in enumerate(top_10_min_points.iterrows()):
            ax.scatter(point['va'], point['ha'], point[difference_col],
                      color=reds[idx], s=150, marker='o', alpha=1.0,  # Full opacity for red points
                      label=f'Top {idx+2} (va={point["va"]}, ha={point["ha"]}, diff={point[difference_col]:.4f})')
            # Add connecting line
            ax.plot([point['va'], point['va']],
                   [point['ha'], point['ha']],
                   [0, point[difference_col]],
                   color=reds[idx], linestyle='--', alpha=0.5)
        
        # Highlight minimum point
        ax.scatter(min_point['va'], min_point['ha'], min_point[difference_col],
                  color='darkred', s=200, marker='*', alpha=1.0,  # Full opacity for minimum point
                  label=f'Minimum (va={min_point["va"]}, ha={min_point["ha"]}, diff={min_point[difference_col]:.4f})')
        
        # Add connecting line to minimum point
        ax.plot([min_point['va'], min_point['va']],
                [min_point['ha'], min_point['ha']],
                [0, min_point[difference_col]],
                color='darkred', linestyle='--', alpha=0.7)
        
        # Labels and title
        ax.set_xlabel('Vertical Angle (va)', fontsize=12, labelpad=10)
        ax.set_ylabel('Horizontal Angle (ha)', fontsize=12, labelpad=10)
        ax.set_zlabel(zlabel, fontsize=12, labelpad=10)
        plt.title(title + '\n(showing only differences < 1)', fontsize=14, pad=20)
        
        # Add legend with scrollbar if needed
        ax.legend(fontsize=8, bbox_to_anchor=(1.15, 1), loc='upper left')
        
        # Adjust view angle for better visualization
        ax.view_init(elev=20, azim=45)
        
        # Add grid
        ax.grid(True)
        
        plt.tight_layout()
        return min_point, max_point, top_10_min_points
    
    # Create first plot
    min_diff1_point, max_diff1_point, top_10_min_diff1 = create_3d_plot(
        'diff1_delta',
        'Difference 1: Minimum Length vs Strand Width\n|min_length - 2*strand_width| comparison between horizontal and vertical',
        'Difference 1\n(lower is better)'
    )
    plt.show()
    
    # Create second plot
    min_diff2_point, max_diff2_point, top_10_min_diff2 = create_3d_plot(
        'diff2_delta',
        'Difference 2: Length Consistency\n|max_length - min_length| comparison between horizontal and vertical',
        'Difference 2\n(lower is better)'
    )
    plt.show()
    
    # Print the details of minimum, maximum, and top 10 points
    print("\nBest configurations found:")
    
    print("\nFor Difference 1 (Minimum Length vs Strand Width):")
    print("This measures how close the minimum length is to twice the strand width")
    print("comparing horizontal and vertical alignments.")
    print("-" * 50)
    print("MINIMUM:")
    print(f"Vertical Angle: {min_diff1_point['va']}")
    print(f"Horizontal Angle: {min_diff1_point['ha']}")
    print(f"Difference: {min_diff1_point['diff1_delta']:.4f}")
    print(f"Vertical diff1: {min_diff1_point['diff1_v']:.4f}")
    print(f"Horizontal diff1: {min_diff1_point['diff1_h']:.4f}")
    print("\nMAXIMUM:")
    print(f"Vertical Angle: {max_diff1_point['va']}")
    print(f"Horizontal Angle: {max_diff1_point['ha']}")
    print(f"Difference: {max_diff1_point['diff1_delta']:.4f}")
    print("\nTOP 10 NEXT BEST VALUES:")
    for idx, point in top_10_min_diff1.iterrows():
        print(f"{idx+2}. va={point['va']}, ha={point['ha']}, diff={point['diff1_delta']:.4f}")
    
    print("\nFor Difference 2 (Length Consistency):")
    print("This measures the consistency of strand lengths by comparing")
    print("the difference between maximum and minimum lengths in both directions.")
    print("-" * 50)
    print("MINIMUM:")
    print(f"Vertical Angle: {min_diff2_point['va']}")
    print(f"Horizontal Angle: {min_diff2_point['ha']}")
    print(f"Difference: {min_diff2_point['diff2_delta']:.4f}")
    print(f"Vertical diff2: {min_diff2_point['diff2_v']:.4f}")
    print(f"Horizontal diff2: {min_diff2_point['diff2_h']:.4f}")
    print("\nMAXIMUM:")
    print(f"Vertical Angle: {max_diff2_point['va']}")
    print(f"Horizontal Angle: {max_diff2_point['ha']}")
    print(f"Difference: {max_diff2_point['diff2_delta']:.4f}")
    print("\nTOP 10 NEXT BEST VALUES:")
    for idx, point in top_10_min_diff2.iterrows():
        print(f"{idx+2}. va={point['va']}, ha={point['ha']}, diff={point['diff2_delta']:.4f}")

if __name__ == "__main__":
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\m1xn2_rh_continuation"
    df = collect_va_ha_from_directory(base_dir)
    if df is not None:
        plot_va_vs_ha(df)
