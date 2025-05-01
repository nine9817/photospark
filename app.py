import os
from flask import Flask, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

REMOVE_BG_API_KEY = os.getenv("REMOVE_BG_API_KEY")

@app.route('/')
def home():
    return jsonify({"message": "Image Enhancer Bot is live."})

@app.route('/upload', methods=['POST'])
def upload():
    image_file = request.files['image_file']
    bg_style = request.form['bg_style']
    overlay_text = request.form.get('overlay_text', '')
    output_format = request.form['output_format']
    logo_file = request.files.get('logo_file')

    # Set output size
    format_map = {
        'hero': (1600, 900),
        'body': (1200, 900),
        'square': (1080, 1080),
        'portrait': (1080, 1350),
        'print': (2550, 3300),  # 8.5 x 11 inches at 300 DPI
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
        return jsonify({"error": response.text}), 400

    result_image = Image.open(BytesIO(response.content)).convert('RGBA')

    # Create new background
    bg = Image.new('RGBA', bg_size, (255, 255, 255, 255))
    offset = ((bg_size[0] - result_image.width) // 2, (bg_size[1] - result_image.height) // 2)
    bg.paste(result_image, offset, result_image)

    # Add logo if provided
    if logo_file:
        logo = Image.open(logo_file).convert("RGBA")
        logo.thumbnail((150, 150))
        bg.paste(logo, (bg_size[0] - logo.width - 20, bg_size[1] - logo.height - 20), logo)

    # Add overlay text if any
    if overlay_text:
        draw = ImageDraw.Draw(bg)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        draw.text((30, 30), overlay_text, font=font, fill="black")

    output_path = f"final_output_{output_format}.png"
    bg.convert("RGB").save(output_path, "PNG")
    return send_file(output_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
