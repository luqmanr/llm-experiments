import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from paddleocr import PaddleOCR

def draw_ocr_overlay(image_path, result_objects, output_path="flowmeter_overlay.png"):
    """
    Parses the result structure from PaddleOCR results and renders 
    an overlay of bounding boxes and text.
    """
    # Load the original image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Could not load image at {image_path}")
        return

    # 1. Prepare a base for drawing boxes (BGR)
    overlay = image.copy()
    
    # 2. Setup PIL for high-quality text rendering
    # We'll create a transparent layer for text and then composite it
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)
    
    try:
        # Common path for Linux, adjust if on Windows/Mac
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()

    # The result_objects is a list of dictionaries based on your log
    for data in result_objects:
        # Extract fields directly from the dictionary
        polygons = data.get('dt_polys', [])     # Detection Polygons
        texts = data.get('rec_texts', [])       # Recognition Texts
        scores = data.get('rec_scores', [])     # Confidence Scores
        
        for i in range(len(polygons)):
            # Convert polygon points to integer numpy array
            box = np.array(polygons[i]).astype(np.int32)
            txt = texts[i] if i < len(texts) else ""
            score = scores[i] if i < len(scores) else 0.0

            # --- Draw Box on CV2 Overlay ---
            # Green for high confidence (>0.8), Orange otherwise
            color_bgr = (0, 255, 0) if score > 0.8 else (0, 165, 255)
            
            # Thick outline
            cv2.polylines(overlay, [box], isClosed=True, color=color_bgr, thickness=3)
            # Fill for transparency
            cv2.fillPoly(overlay, [box], color=color_bgr)

            # --- Draw Text on PIL Layer ---
            # Use top-left corner of the polygon
            anchor_x, anchor_y = int(box[0][0]), int(box[0][1])
            label = f"{txt} ({score:.2f})"
            
            # Background rectangle for text legibility
            try:
                # Use textbbox to get dimensions (Pillow 10+)
                bbox = draw.textbbox((anchor_x, anchor_y - 25), label, font=font)
                draw.rectangle(bbox, fill=(0, 0, 0))
            except AttributeError:
                # Fallback for older Pillow
                draw.rectangle([anchor_x, anchor_y - 25, anchor_x + 180, anchor_y], fill=(0, 0, 0))
                
            draw.text((anchor_x, anchor_y - 25), label, font=font, fill=(255, 255, 255))

    # 3. Blend the boxes (alpha transparency)
    alpha = 0.3
    blended_boxes = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    
    # 4. Composite the text back onto the blended image
    # Convert the PIL image (with text) back to CV2 format
    text_overlay_bgr = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    
    # We want the text to be opaque, so we'll use it where it's not original-image pixels
    # Or more simply, combine the text_overlay with the blended_boxes
    final_output = cv2.addWeighted(text_overlay_bgr, 0.7, blended_boxes, 0.3, 0)

    # Save the result
    cv2.imwrite(output_path, final_output)
    print(f"Visualization saved to {output_path}")

# --- Execution ---

# Initialize PaddleOCR
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False
)

# Run inference
image_filename = "flowmeter-1.png"
# This typically returns a list of dictionaries in your current environment
result = ocr.predict(input=image_filename)

# Parse and Render
draw_ocr_overlay(image_filename, result)