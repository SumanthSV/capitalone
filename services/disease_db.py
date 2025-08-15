
# services/disease_db.py
import os
import cv2
import numpy as np
from utils.image_processing import get_dominant_colors
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000

class DiseaseDatabase:
    def __init__(self, dataset_path="disease_dataset"):
        print(f"[DEBUG] Loading dataset from: {os.path.abspath(dataset_path)}")
        self.dataset = self._load_dataset(dataset_path)
        print(f"[DEBUG] Loaded {len(self.dataset)} images")
        # Print first 5 items for verification
        for i, item in enumerate(self.dataset[:5]):
            print(f"[DEBUG] Item {i+1}: {item['crop']} - {item['disease']} - {item['image_path']}")
    
    def _load_dataset(self, path):
        """Load dataset with flexible structure to handle your custom additions"""
        dataset = []
        
        # Case 1: Crop-specific folders (Tomato, Rice, etc.)
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            
            if os.path.isdir(item_path):
                # Case 1a: Crop/Disease/Images structure
                if any(os.path.isdir(os.path.join(item_path, sub)) for sub in os.listdir(item_path)):
                    for disease_dir in os.listdir(item_path):
                        disease_path = os.path.join(item_path, disease_dir)
                        if os.path.isdir(disease_path):
                            dataset += self._process_disease_folder(disease_path, crop=item, disease=disease_dir)
                
                # Case 1b: Direct disease folders
                elif "disease" in item.lower() or "healthy" in item.lower():
                    dataset += self._process_disease_folder(item_path, disease=item)
                
                # Case 1c: Crop folder with mixed images
                else:
                    dataset += self._process_disease_folder(item_path, crop=item)
        
        return dataset

    def _process_disease_folder(self, folder_path, crop=None, disease=None):
        """Process a folder of disease images"""
        images = []
        for img_file in os.listdir(folder_path):
            if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                img_path = os.path.join(folder_path, img_file)
                try:
                    hex_codes = get_dominant_colors(img_path)
                    images.append({
                        "crop": crop,
                        "disease": disease or os.path.basename(folder_path),
                        "image_path": img_path,
                        "hex_signatures": hex_codes
                    })
                except Exception as e:
                    print(f"Error processing {img_path}: {str(e)}")
        return images

    # services/disease_db.py (updated match_image method)
    def match_image(self, user_img_path, threshold=100):
        try:
            user_hex = get_dominant_colors(user_img_path)
            best_match = None
            min_distance = float('inf')
            
            print(f"[DEBUG] Matching image: {user_img_path}")
            print(f"[DEBUG] User colors: {user_hex}")
            
            for item in self.dataset:
                for db_hex in item["hex_signatures"]:
                    for u_hex in user_hex:
                        dist = self._color_distance(db_hex, u_hex)
                        if dist < min_distance:
                            min_distance = dist
                            best_match = item
                            print(f"[DEBUG] New best match: {item['image_path']} (distance: {dist:.2f})")
            
            print(f"[DEBUG] Final match distance: {min_distance:.2f}")
            
            # Try filename matching if color match fails
            if min_distance >= threshold:
                user_filename = os.path.basename(user_img_path)
                print(f"[DEBUG] Trying filename match: {user_filename}")
                for item in self.dataset:
                    db_filename = os.path.basename(item["image_path"])
                    if user_filename.lower() == db_filename.lower():
                        print(f"[DEBUG] Filename match found: {db_filename}")
                        return item
            
            return best_match if min_distance < threshold else None
        except Exception as e:
            print(f"[ERROR] Matching error: {str(e)}")
            return None

    # services/disease_db.py


    def _color_distance(self, hex1, hex2):
        """Calculate Euclidean distance between two hex colors"""
        try:
            hex1 = hex1.lstrip('#')
            hex2 = hex2.lstrip('#')
            rgb1 = np.array([int(hex1[i:i+2], 16) for i in (0, 2, 4)])
            rgb2 = np.array([int(hex2[i:i+2], 16) for i in (0, 2, 4)])
            return np.linalg.norm(rgb1 - rgb2)  # Euclidean distance
        except Exception as e:
            print(f"Color distance error: {str(e)}")
            return float('inf')

# Initialize database
disease_db = DiseaseDatabase()
