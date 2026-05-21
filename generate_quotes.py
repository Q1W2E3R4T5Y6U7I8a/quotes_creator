import json
import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import textwrap

def get_random_image(image_folder, used_images=set()):
    """Get a random JPG image from the folder that hasn't been used yet"""
    # Get all JPG files
    image_files = [f for f in os.listdir(image_folder) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        return None
    
    # Remove used images from available options
    available_files = [f for f in image_files if f not in used_images]
    
    # If we've used all images, reset and allow reuse
    if not available_files:
        available_files = image_files
        used_images.clear()
    
    # Select random image
    selected_image = random.choice(available_files)
    used_images.add(selected_image)
    
    return os.path.join(image_folder, selected_image), selected_image

def crop_to_square(image):
    """Crop image to square (center crop)"""
    width, height = image.size
    
    if width == height:
        return image
    
    # Get the minimum dimension
    min_dim = min(width, height)
    
    # Calculate cropping coordinates (center crop)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    
    return image.crop((left, top, right, bottom))

def calculate_centered_layout(quote_lines, quote_font, author_font, number_font, 
                             quote_number, total_quotes, emblem_height=0):
    """Calculate all positions for centered layout"""
    # Calculate quote dimensions
    line_height = 70
    quote_spacing = 10
    quote_line_heights = []
    
    for line in quote_lines:
        bbox = quote_font.getbbox(line)
        quote_line_heights.append(bbox[3] - bbox[1])
    
    total_quote_height = sum(quote_line_heights) + ((len(quote_lines) - 1) * quote_spacing)
    
    # Calculate author dimensions
    author_bbox = author_font.getbbox("Author")
    author_height = author_bbox[3] - author_bbox[1]
    
    # Calculate counter dimensions
    counter_text = f"{quote_number}"
    total_text = f"/{total_quotes}"
    
    counter_bbox = number_font.getbbox(counter_text)
    counter_height = counter_bbox[3] - counter_bbox[1]
    counter_width = counter_bbox[2] - counter_bbox[0]
    
    total_bbox = author_font.getbbox(total_text)
    total_width = total_bbox[2] - total_bbox[0]
    
    # Calculate total content height
    content_height = (
        total_quote_height +  # Quote
        60 +                  # Space between quote and author
        author_height +       # Author
        20 +                  # Author decoration line height
        60                    # Bottom margin for emblem
    )
    
    # If emblem exists, account for its height
    if emblem_height > 0:
        content_height += emblem_height
    
    # Calculate starting Y position for centered content
    total_height = 1024
    y_start = (total_height - content_height) // 2
    
    return {
        'y_start': y_start,
        'line_height': line_height,
        'quote_spacing': quote_spacing,
        'quote_line_heights': quote_line_heights,
        'total_quote_height': total_quote_height,
        'author_height': author_height,
        'counter_width': counter_width,
        'total_width': total_width,
        'content_height': content_height
    }

def create_quote_image(quote_data, image_path, output_path, quote_number, total_quotes=365):
    """Create a quote image with the given background - CENTERED LAYOUT VERSION"""
    # Open the image
    img = Image.open(image_path).convert('RGB')
    
    # CUTTING TO SQUARE FIRST - This is the key change
    img = crop_to_square(img)
    
    # Resize to exactly 1024x1024
    img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
    
    # Now apply all effects and overlays
    # Apply opacity by reducing brightness/contrast
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.7)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(0.8)
    
    # Add a semi-transparent dark overlay for better text readability
    overlay = Image.new('RGBA', (1024, 1024), (0, 0, 0, 128))
    img_rgba = img.convert('RGBA')
    img = Image.alpha_composite(img_rgba, overlay).convert('RGB')
    
    # Convert back to RGBA for working with PNG overlays
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)
    
    # Load Kurale font
    kurale_paths = [
        "./Kurale-Regular.ttf"
    ]
    
    quote_font = None
    author_font = None
    number_font = None
    
    for font_path in kurale_paths:
        try:
            # Beautiful font sizes for different elements
            quote_font = ImageFont.truetype(font_path, 46)
            author_font = ImageFont.truetype(font_path, 38)
            number_font = ImageFont.truetype(font_path, 72)  # Big font for counter
            break
        except:
            continue
    
    if quote_font is None:
        # Fallback fonts
        fallback_fonts = [
            "arial.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "C:\\Windows\\Fonts\\georgia.ttf",
        ]
        for font_path in fallback_fonts:
            try:
                quote_font = ImageFont.truetype(font_path, 46)
                author_font = ImageFont.truetype(font_path, 38)
                number_font = ImageFont.truetype(font_path, 72)
                break
            except:
                continue
    
    if quote_font is None:
        quote_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
        number_font = ImageFont.load_default()
    
    # Extract data and clean it
    quote = quote_data.get("quote", "").strip()
    author = quote_data.get("author", "").strip()
    
    # Remove trailing dots from quote and author
    quote = quote.rstrip('.')
    author = author.rstrip('.')
    
    # Text colors
    quote_text_color = (255, 255, 255, 255)
    author_text_color = (255, 255, 255, 255)
    counter_text_color = (255, 255, 255, 255)
    total_text_color = (255, 255, 255, 255)
    shadow_color = (0, 0, 0, 180)
    
    # Wrap quote text
    max_chars_per_line = 38
    wrapped_quote = textwrap.fill(quote, width=max_chars_per_line)
    quote_lines = wrapped_quote.split('\n')
    
    # Check for emblem and get its dimensions
    emblem = None
    emblem_height = 0
    emblem_width = 0
    if os.path.exists("emblem.png"):
        try:
            emblem = Image.open("emblem.png").convert("RGBA")
            # Resize emblem to elegant size
            emblem_size = min(350, 300)
            emblem.thumbnail((emblem_size, emblem_size), Image.Resampling.LANCZOS)
            emblem_width, emblem_height = emblem.size
        except Exception as e:
            print(f"Could not load emblem.png: {e}")
    
    # Calculate centered layout
    layout = calculate_centered_layout(quote_lines, quote_font, author_font, 
                                      number_font, quote_number, total_quotes, emblem_height)
    
    y_start = layout['y_start']
    
    # 1. ADD OPENING QUOTE (if exists)
    opening_quote = None
    quote_size = 80
    if os.path.exists("opening_quote.png"):
        try:
            opening_quote = Image.open("opening_quote.png").convert("RGBA")
            opening_quote.thumbnail((quote_size, quote_size), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"Could not load opening_quote.png: {e}")
    
    # Draw quote text with centered layout
    current_y = y_start
    for i, line in enumerate(quote_lines):
        bbox = quote_font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        text_height = layout['quote_line_heights'][i]
        x_position = (1024 - text_width) // 2
        y_position = current_y
        
        # Add opening quote mark for first line
        if i == 0 and opening_quote:
            opening_x = x_position - opening_quote.width - 20
            opening_y = y_position + (text_height - opening_quote.height) // 2
            img.paste(opening_quote, (opening_x, opening_y), opening_quote)
        
        # Draw shadow with offset
        draw.text((x_position + 3, y_position + 3), line, font=quote_font, fill=shadow_color)
        
        # Draw main text
        draw.text((x_position, y_position), line, font=quote_font, fill=quote_text_color)
        
        # Move to next line
        current_y += text_height + layout['quote_spacing']
    
    # Add closing quote mark for last line
    if os.path.exists("closing_quote.png"):
        try:
            closing_quote = Image.open("closing_quote.png").convert("RGBA")
            closing_quote.thumbnail((quote_size, quote_size), Image.Resampling.LANCZOS)
            
            # Get last line position
            last_line_bbox = quote_font.getbbox(quote_lines[-1])
            last_line_width = last_line_bbox[2] - last_line_bbox[0]
            last_line_x = (1024 - last_line_width) // 2
            
            closing_x = last_line_x + last_line_width + 20
            closing_y = y_start + layout['total_quote_height'] - closing_quote.height - 10
            
            img.paste(closing_quote, (closing_x, closing_y), closing_quote)
            
        except Exception as e:
            print(f"Could not load closing_quote.png: {e}")
    
    # Draw author with style (centered)
    author_text = author
    author_bbox = author_font.getbbox(author_text)
    author_width = author_bbox[2] - author_bbox[0]
    author_height = author_bbox[3] - author_bbox[1]
    
    author_x = (1024 - author_width) // 2
    author_y = y_start + layout['total_quote_height'] + 60
    
    # Draw author decoration line
    line_length = 100
    line_y = author_y - 20
    draw.line([(author_x - line_length - 20, line_y), 
               (author_x - 10, line_y)], fill=(22, 145, 217, 255), width=2)
    draw.line([(author_x + author_width + 10, line_y), 
               (author_x + author_width + line_length + 20, line_y)], 
              fill=(22, 145, 217, 255), width=2)
    
    # Draw author with effects
    draw.text((author_x + 3, author_y + 3), author_text, font=author_font, fill=shadow_color)
    draw.text((author_x, author_y), author_text, font=author_font, fill=author_text_color)
    
    # 3. ADD COUNTER (top right corner)
    counter_text = f"{quote_number}"
    total_text = f"/{total_quotes}"
    
    # Position: Top right (fixed position, not centered)
    counter_x = 1024 - layout['counter_width'] - layout['total_width'] - 80
    counter_y = 60
    
    # Draw number (big and bold)
    draw.text((counter_x + 2, counter_y + 2), counter_text, font=number_font, fill=shadow_color)
    draw.text((counter_x, counter_y), counter_text, font=number_font, fill=counter_text_color)
    
    # Draw slash and total
    slash_x = counter_x + layout['counter_width']
    draw.text((slash_x, counter_y + 20), total_text, font=author_font, fill=total_text_color)
    
    # 4. ADD EMBLEM (centered at bottom)
    if emblem:
        emblem_x = (1024 - emblem_width) // 2
        emblem_y = 1024 - emblem_height - 40  # 40px from bottom
        img.paste(emblem, (emblem_x, emblem_y), emblem)
    
    # Add subtle vignette effect for more depth
    vignette = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    draw_vignette = ImageDraw.Draw(vignette)
    
    center_x, center_y = 512, 512
    max_radius = 1024 * 0.7
    
    for radius in range(0, int(max_radius), 5):
        alpha = int(40 * (radius / max_radius))
        bbox = (center_x - radius, center_y - radius, 
                center_x + radius, center_y + radius)
        draw_vignette.ellipse(bbox, outline=(0, 0, 0, alpha), width=10)
    
    img = Image.alpha_composite(img, vignette)
    
    # Save image with maximum quality
    img = img.convert('RGB')
    img.save(output_path, 'JPEG', quality=98, optimize=True)

def main():
    json_file = "quotes.json"
    image_folder = "dumy_quotes_images"
    output_folder = "output_quotes"
    
    # CONFIGURABLE SETTINGS
    VARIANTS_PER_QUOTE = 3  # Change this value to 1, 2, 3, 4, 5, etc.
    TOTAL_QUOTES = 365  # Total number in counter (e.g., 1/365)
    
    with open(json_file, 'r', encoding='utf-8') as f:
        quotes_data = json.load(f)
    
    os.makedirs(output_folder, exist_ok=True)
    
    total_actual_quotes = len(quotes_data)
    
    # Track used images to avoid immediate reuse
    used_images = set()
    
    print(f"📊 Processing {total_actual_quotes} quotes...")
    print(f"🎲 Each quote will get {VARIANTS_PER_QUOTE} random background images")
    print(f"📏 All output images will be 1024x1024 squares")
    print(f"🎯 Using CENTERED LAYOUT for all elements")
    print("=" * 50)
    
    for i, quote_data in enumerate(quotes_data, 1):
        quote_number = i
        
        print(f"\n📝 Quote {quote_number}/{total_actual_quotes}:")
        print(f"   '{quote_data.get('quote', '')[:50]}...'")
        
        # Create N different images for this quote
        for variant in range(1, VARIANTS_PER_QUOTE + 1):
            # Get random image for this variant
            random_image_result = get_random_image(image_folder, used_images)
            
            if random_image_result:
                image_path, image_name = random_image_result
                
                # Create output filename
                if VARIANTS_PER_QUOTE > 1:
                    output_filename = f"quote_{quote_number:03d}_{variant}.jpg"
                else:
                    output_filename = f"quote_{quote_number:03d}.jpg"
                    
                output_path = os.path.join(output_folder, output_filename)
                
                # Create the image
                create_quote_image(quote_data, image_path, output_path, 
                                  quote_number, TOTAL_QUOTES)
                
                print(f"   ✓ Created image {variant}/{VARIANTS_PER_QUOTE}: {output_filename}")
            else:
                print(f"   ✗ No images found in folder for variant {variant}")
    
    print("\n" + "=" * 50)
    print(f"✅ All done! Created {total_actual_quotes * VARIANTS_PER_QUOTE} images")
    print(f"   - {total_actual_quotes} quotes")
    print(f"   - {VARIANTS_PER_QUOTE} variants per quote")
    print(f"   - Random backgrounds for each variant")
    print(f"   - All images are 1024x1024 squares")
    print(f"   - CENTERED LAYOUT for text, emblem, and quote marks")
    print(f"   - Output folder: '{output_folder}'")

if __name__ == "__main__":
    # Set random seed for reproducibility (optional)
    # random.seed(42)  # Uncomment for consistent results
    
    main()