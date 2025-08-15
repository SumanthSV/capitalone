# utils/image_processing.py
import cv2
import numpy as np
from sklearn.cluster import KMeans


def get_dominant_colors(image_path, n_colors=5):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")
    
    # Convert to RGB color space (OpenCV uses BGR by default)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Resize for faster processing
    img = cv2.resize(img, (300, 300))
    pixels = img.reshape(-1, 3)
    
    # Get dominant colors
    kmeans = KMeans(n_clusters=n_colors, n_init=10)
    kmeans.fit(pixels)
    
    # Convert to hex codes
    hex_codes = []
    for center in kmeans.cluster_centers_:
        # Convert float to int and clamp to 0-255 range
        r, g, b = [int(max(0, min(255, c))) for c in center]
        hex_codes.append(f"#{r:02x}{g:02x}{b:02x}")
    
    return hex_codes