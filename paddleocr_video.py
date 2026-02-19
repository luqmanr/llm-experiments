import cv2
import numpy as np
import os
import shutil
from PIL import Image, ImageDraw, ImageFont
from paddleocr import PaddleOCR

def process_frame(image, result_objects, font):
    """
    Renders OCR results onto a single frame (numpy array).
    """
    # 1. Prepare overlay for boxes
    overlay = image.copy()
    
    # 2. Setup PIL for text
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)

    for data in result_objects:
        polygons = data.get('dt_polys', [])
        texts = data.get('rec_texts', [])
        scores = data.get('rec_scores', [])
        
        for i in range(len(polygons)):
            box = np.array(polygons[i]).astype(np.int32)
            txt = texts[i] if i < len(texts) else ""
            score = scores[i] if i < len(scores) else 0.0

            # Draw Box
            color_bgr = (0, 255, 0) if score > 0.8 else (0, 165, 255)
            cv2.polylines(overlay, [box], isClosed=True, color=color_bgr, thickness=2)
            cv2.fillPoly(overlay, [box], color=color_bgr)

            # Draw Text
            anchor_x, anchor_y = int(box[0][0]), int(box[0][1])
            label = f"{txt} ({score:.2f})"
            
            try:
                bbox = draw.textbbox((anchor_x, anchor_y - 25), label, font=font)
                draw.rectangle(bbox, fill=(0, 0, 0))
            except AttributeError:
                draw.rectangle([anchor_x, anchor_y - 25, anchor_x + 150, anchor_y], fill=(0, 0, 0))
                
            draw.text((anchor_x, anchor_y - 25), label, font=font, fill=(255, 255, 255))

    # Blend and combine
    alpha = 0.3
    blended_boxes = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    text_layer_bgr = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)
    
    # Merge text layer and blended boxes
    return cv2.addWeighted(text_layer_bgr, 0.7, blended_boxes, 0.3, 0)

def process_video(video_path, output_path="output_ocr_video.mp4", frame_skip=2, debug_dir="ocr_debug_frames"):
    """
    Reads a video file, runs OCR on every Nth frame, and saves intermediate images 
    to a debug directory before encoding the final video.
    """
    # Initialize OCR
    ocr = PaddleOCR(use_doc_orientation_classify=False, use_textline_orientation=False)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return

    # Handle debug directory
    if os.path.exists(debug_dir):
        shutil.rmtree(debug_dir)
    os.makedirs(debug_dir)

    # Get video properties
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps    = cap.get(cv2.CAP_PROP_FPS)
    
    # Load font once
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 20)
    except:
        font = ImageFont.load_default()

    print(f"Processing video with frame_skip={frame_skip}...")
    
    frame_count = 0
    processed_frame_paths = []
    last_result = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Frame Skip Logic: Only run OCR inference every 'frame_skip' frames
        if frame_count % frame_skip == 0:
            last_result = ocr.predict(input=frame)
        
        # Render using the most recent OCR results (interpolation of sorts)
        processed_frame = process_frame(frame, last_result, font)
        
        # Save frame to temporary directory for debugging
        frame_filename = os.path.join(debug_dir, f"frame_{frame_count:05d}.jpg")
        cv2.imwrite(frame_filename, processed_frame)
        processed_frame_paths.append(frame_filename)
            
        frame_count += 1
        if frame_count % 10 == 0:
            print(f"Processed {frame_count} frames...")

    cap.release()

    # --- Re-encode Video from Saved Frames ---
    print("Encoding video from debug frames...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for path in processed_frame_paths:
        img = cv2.imread(path)
        out.write(img)

    out.release()
    cv2.destroyAllWindows()
    
    print(f"Video processing complete.")
    print(f"Final video: {output_path}")
    print(f"Debug frames available in: {debug_dir}")

# --- Execution ---
video_input = "flowmeter-video-1.mp4" # Path to your video file
# frame_skip=2 means OCR runs on frames 0, 2, 4... and the results are applied to the next frame too
process_video(video_input, frame_skip=2)