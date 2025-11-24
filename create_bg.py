from PIL import Image, ImageDraw
import os

def create_pastel_stripe_bg(width=1200, height=800):
    # Colors
    bg_color = (255, 255, 255) # White
    # Pastel Yellow-Green (Fresh and bright)
    stripe_color = (210, 245, 180) 
    
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Draw diagonal stripes
    # To ensure equal width, the step should be 2 * width_stripe
    # However, draw.line width is the stroke width.
    # If we want visual equal width, we need to account for geometry.
    # But for simple 45 degree (approx) lines, step = 2 * width works well enough visually if we ignore the angle projection for a moment,
    # or just trust the stroke width.
    
    stripe_width = 50
    step = stripe_width * 2
    
    # We need to cover the whole rotation
    for i in range(-height, width + height, step):
        draw.line([(i, 0), (i + height, height)], fill=stripe_color, width=stripe_width)

    # Save
    base_dir = os.path.dirname(os.path.abspath(__file__))
    asset_dir = os.path.join(base_dir, "asset")
    if not os.path.exists(asset_dir):
        os.makedirs(asset_dir)
        
    save_path = os.path.join(asset_dir, "bg.png")
    image.save(save_path)
    print(f"Background saved to {save_path}")

if __name__ == "__main__":
    create_pastel_stripe_bg()
