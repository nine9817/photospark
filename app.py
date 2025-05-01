import os
from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")

@app.route('/upload', methods=['POST'])
def upload():
    print("🔥 /upload route was hit")  # Debug line

    try:
        image_file = request.files['image_file']
    except Exception as e:
        print("❌ image_file not found:", str(e))
        return jsonify({"error": "Missing product image (image_file)"}), 400

    try:
        bg_style = request.form['bg_style']
        overlay_text = request.form.get('overlay_text', '')
        output_format = request.form['output_format']
        logo_file = request.files.get('logo_file')
    except Exception as e:
        print("❌ Form field error:", str(e))
        return jsonify({"error": "Missing one or more form fields"}), 400

    print(f"✅ Fields received: bg_style={bg_style}, output_format={output_format}, overlay_text={overlay_text}")

    # Background size setup
    format_map = {
        'hero': (1600, 900),
        'body': (1200, 900),
        'square': (1080, 1080),
        'portrait': (1080, 1350),
        'print': (2550, 3300),
    }
    bg_size = format_map.get(output_format, (1080, 1350))

    # Remove background
    response = requests.post(
        'https://api.remove.bg/v1.0/removebg',
        files={'image_file': image_file},
        data={'size': 'auto'},
        headers={'X-Api-Key': REMOVE_BG_API_KEY}
    )

    if response.status_code != 200:
        print("❌ Remove.bg error:", response.text)
        return jsonify({"error": response.text}), 400

    result_image = Image.open(BytesIO(response.content)).convert('RGBA')

    # Build background
    bg = Image.new('RGBA', bg_size, (255, 255, 255, 255))
    offset = ((bg_size[0] - result_image.width) // 2, (bg_size[1] - result_image.height) // 2)
    bg.paste(result_image, offset, result_image)

    # Add logo
    if logo_file:
        try:
            logo = Image.open(logo_file).convert("RGBA")
            logo.thumbnail((150, 150))
            bg.paste(logo, (bg_size[0] - logo.width - 20, bg_size[1] - logo.height - 20), logo)
        except Exception as e:
            print("⚠️ Error processing logo:", str(e))

    # Add overlay text
    if overlay_text:
        try:
            draw = ImageDraw.Draw(bg)
            font = ImageFont.truetype("arial.ttf", 40)
            draw.text((30, 30), overlay_text, font=font, fill="black")
        except:
            draw = ImageDraw.Draw(bg)
            draw.text((30, 30), overlay_text, fill="black")

    output_path = f"final_output_{output_format}.png"
    bg.convert("RGB").save(output_path, "PNG")
    print("✅ Image processed and saved:", output_path)

    return send_file(output_path, mimetype='image/png')

