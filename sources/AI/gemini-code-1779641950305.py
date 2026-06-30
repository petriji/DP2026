#!/usr/bin/env python3
"""
Ternary Economic Balance Visualizer for EU27 (2026 Model)
Author: CTU/CVUT PRI Diploma Thesis Framework
Description: Generates a mathematically precise ternary diagram with an RGB 
             background continuum representing actor dominance:
             - Red (R): Household/Employee Potential (Axis A)
             - Green (G): State/Government Potential (Axis C)
             - Blue (B): Corporate Capital/Employer Potential (Axis B)
Outputs a standalone PGF file for native vector rendering inside LaTeX.
"""

import numpy as np
import matplotlib
# Enforce the PGF backend to guarantee seamless vector integration with LaTeX
matplotlib.use("pgf")
import matplotlib.pyplot as plt

# PGF and LaTeX font rendering synchronization configurations
matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    "font.family": "serif",
    "text.usetex": True,
    "pgf.rcfonts": False,
})

# =============================================================================
# 1. GEOMETRY AND MESH CONFIGURATION
# =============================================================================
# Define the vertices of the equilateral triangle in Cartesian space (Side = 1.0)
# Vertex B: Employers (Bottom-Left)
# Vertex C: State (Bottom-Right)
# Vertex A: Employees (Top-Center)
B_xy = np.array([0.0, 0.0])
C_xy = np.array([1.0, 0.0])
A_xy = np.array([0.5, np.sqrt(3)/2])

# Resolution setup for the pixel background grid
resolution = 800  
x_grid = np.linspace(0.0, 1.0, resolution)
y_grid = np.linspace(0.0, np.sqrt(3)/2, resolution)
X, Y = np.meshgrid(x_grid, y_grid)

# =============================================================================
# 2. BARYCENTRIC COORDINATE TRANSFORM & RGB MAPPING
# =============================================================================
# Linear algebra determinant for Cartesian to Barycentric mapping
determinant = (C_xy[1] - B_xy[1]) * (A_xy[0] - B_xy[0]) + (B_xy[0] - C_xy[0]) * (A_xy[1] - B_xy[1])

# Calculate ternary weights (w_A, w_B, w_C) for every pixel point
w_A = ((C_xy[1] - B_xy[1]) * (X - B_xy[0]) + (B_xy[0] - C_xy[0]) * (Y - B_xy[1])) / determinant
w_B = ((B_xy[1] - A_xy[1]) * (X - B_xy[0]) + (A_xy[0] - B_xy[0]) * (Y - B_xy[1])) / determinant
w_C = 1.0 - w_A - w_B

# Mask out pixels falling outside the boundaries of the equilateral triangle
inside_mask = (w_A >= 0) & (w_B >= 0) & (w_C >= 0)

# Inject RGB channel balances matching the rigorous analytical assignment:
# Red -> Axis A (Employees), Green -> Axis C (State), Blue -> Axis B (Employers)
R_channel = np.clip(w_A, 0, 1)
G_channel = np.clip(w_C, 0, 1)
B_channel = np.clip(w_B, 0, 1)
Alpha_channel = np.where(inside_mask, 1.0, 0.0) # Set background mask to fully transparent

# Stack matrix arrays to build the multi-channel RGBA master image
rgba_heatmap = np.stack([R_channel, G_channel, B_channel, Alpha_channel], axis=-1)

# =============================================================================
# 3. PLOT INITIALIZATION & BACKGROUND RENDERING
# =============================================================================
fig, ax = plt.subplots(figsize=(6.5, 5.5))
ax.imshow(rgba_heatmap, origin='lower', extent=[0, 1, 0, np.sqrt(3)/2], interpolation='bilinear')

# =============================================================================
# 4. TERNARY TO CARTESIAN MAPPING FUNCTION
# =============================================================================
def transform_ternary_to_cartesian(a, b, c):
    """
    Normalizes and maps ternary coordinate weights (%) onto 2D Cartesian coordinates.
    """
    normalization = a + b + c
    a_weight = a / normalization
    b_weight = b / normalization
    c_weight = c / normalization
    
    # Calculate weighted position center point
    cartesian_point = a_weight * A_xy + b_weight * B_xy + c_weight * C_xy
    return cartesian_point[0], cartesian_point[1]

# =============================================================================
# 5. EMPIRICAL EU27 PANEL PLOTTING
# =============================================================================
# Coordinates extracted directly from the finalized 2026 macro-calibrated model
dataset_eu27 = {
    r"\textbf{CZ} [16, 47, 37]": (16, 47, 37),
    r"\textbf{DK} [33, 33, 34]": (33, 33, 34),
    r"\textbf{SE} [32, 34, 34]": (32, 34, 34),
    r"\textbf{FI} [32, 33, 35]": (32, 33, 35),
    r"\textbf{DE} [41, 30, 29]": (41, 30, 29),
    r"\textbf{FR} [42, 29, 29]": (42, 29, 29),
    r"\textbf{SK} [11, 57, 32]": (11, 57, 32),
    r"\textbf{PL} [16, 56, 28]": (16, 56, 28),
    r"\textbf{BG} [7, 69, 24]":  (7, 69, 24),
    r"\textbf{RO} [11, 63, 26]": (11, 63, 26)
}

# Render data nodes into the space grid matrix
for name, coordinates in dataset_eu27.items():
    pos_x, pos_y = transform_ternary_to_cartesian(*coordinates)
    
    # Plot standard data points (White circle with clear black borders for maximum RGB contrast)
    ax.scatter(pos_x, pos_y, color='white', edgecolors='black', s=40, linewidths=1.2, zorder=5)
    
    # Text labels anchoring with semitransparent boxes to protect LaTeX typography legibility
    ax.text(pos_x + 0.02, pos_y + 0.005, name, fontsize=7.5, zorder=6,
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))

# =============================================================================
# 6. TERNARY GRID LINES SYSTEM
# =============================================================================
# Draw subtle 20% interval internal reference lines across the matrix triangle
for grid_line in [0.2, 0.4, 0.6, 0.8]:
    # Constant Axis A lines (Horizontal orientation)
    ax.plot([grid_line*0.5, 1 - grid_line*0.5], [grid_line*np.sqrt(3)/2, grid_line*np.sqrt(3)/2],
            color='white', linestyle=':', alpha=0.5, linewidth=0.7)
    # Constant Axis B lines
    ax.plot([grid_line, grid_line + (1-grid_line)*0.5], [0, (1-grid_line)*np.sqrt(3)/2],
            color='white', linestyle=':', alpha=0.5, linewidth=0.7)
    # Constant Axis C lines
    ax.plot([grid_line*0.5, grid_line], [grid_line*np.sqrt(3)/2, 0],
            color='white', linestyle=':', alpha=0.5, linewidth=0.7)

# Overlay the thick black framing borders of the main matrix polygon patch
border_triangle = plt.Polygon([B_xy, C_xy, A_xy], fill=False, edgecolor='black', linewidth=1.4, zorder=4)
ax.add_patch(border_triangle)

# =============================================================================
# 7. STRATEGIC IMPULS TRANSFORMATION VECTOR (GREEN ARROW)
# =============================================================================
# Strategic vector path escaping the Middle-Income Trap from CZ coordinates to Nordic Optimum area
start_x, start_y = transform_ternary_to_cartesian(16, 47, 37)
target_x, target_y = transform_ternary_to_cartesian(30, 34, 36)

ax.annotate('', xy=(target_x, target_y), xytext=(start_x, start_y), zorder=7,
            arrowprops=dict(arrowstyle="-|>", color='green!60!black', lw=2.5, mutation_scale=15))
ax.text((start_x + target_x)/2 - 0.05, (start_y + target_y)/2 + 0.03, 
        r'\textbf{Strategic Impuls}', color='green!40!black', fontsize=8, fontweight='bold', rotation=43)

# =============================================================================
# 8. AXIS TYPOGRAPHY LABELS (LATEX COMPATIBLE)
# =============================================================================
ax.text(A_xy[0], A_xy[1] + 0.03, r"\textbf{A: Households / Employees} (Red Component)", ha='center', va='bottom', fontsize=9)
ax.text(B_xy[0] - 0.02, B_xy[1] - 0.02, r"\textbf{B: Employers / Capital}\\(Blue Component)", ha='right', va='top', fontsize=9)
ax.text(C_xy[0] + 0.02, C_xy[1] - 0.02, r"\textbf{C: State / Government}\\(Green Component)", ha='left', va='top', fontsize=9)

# Clean out native Cartesian grids background frames
ax.set_xlim(-0.18, 1.18)
ax.set_ylim(-0.12, 1.02)
ax.axis('off')

# =============================================================================
# 9. STANDALONE PRODUCTION PGF EXPORT
# =============================================================================
output_filename = "ternary_heatmap.pgf"
plt.savefig(output_filename, bbox_inches='tight', backend='pgf')
print(f"Success: Standalone TeX-vector asset compiled to: {output_filename}")