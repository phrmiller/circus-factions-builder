#!/usr/bin/env python3

"""
This script builds the Circus Factions website (circusfactions.net).
Add a `-w` flag to watch for changes and rebuild the site automatically.
The `main()` function describes the steps reasonably well.
If others are reading this, be warned that I'm not much of a programmer.
Note to self: Other notes are in Obsidian; start with "Circus Factions / REAMDE".
"""

# Standard library
import argparse
from collections import Counter
from datetime import datetime
import glob
import html
import json
import os
from pathlib import Path
import shutil
import sys
import time

# Third-party libraries
import bs4
from jinja2 import Environment, FileSystemLoader
import markdown
from PIL import Image
from typogrify.filters import typogrify
import yaml

# Local modules
from modules.watchdog import start_watching

# Constants. Note that `expanduser` is necessary for Ubuntu.
BUILDER_DIRECTORY = Path('~/GitHub/circus-factions-builder').expanduser()
CONTENT_DIRECTORY = Path('~/GitHub/circus-factions-content').expanduser()
SITE_DIRECTORY = Path('~/GitHub/circus-factions-site/public').expanduser()

# Fucntions: Update content files

def convert_images():
    image_directory = CONTENT_DIRECTORY / 'images'
    image_files = glob.glob(os.path.join(image_directory, "*.@(jpg|jpeg|png)"))
    for image_file in image_files:
        file_name = os.path.splitext(os.path.basename(image_file))[0]
        img = Image.open(image_file)
        webp_path = os.path.join(image_directory, f"{file_name}.webp")
        img.save(webp_path, format="WebP", quality=80)
        os.remove(image_file)

def update_markdown_image_links():
    for file in CONTENT_DIRECTORY.glob('**/*.md'):
        with open(file, 'r', encoding="utf-8") as f:
            original_content = f.read()
        updated_content = original_content.replace('.jpg', '.webp')
        updated_content = updated_content.replace('.jpeg', '.webp')
        updated_content = updated_content.replace('.png', '.webp')
        if updated_content != original_content:
            with open(file, 'w', encoding="utf-8") as f:
                f.write(updated_content)

def update_content_files():
    convert_images()
    update_markdown_image_links()

# Functions: Gather content data

def verify_yaml_data(file, file_data):
    for key in ['description', 'tags', 'uuid', 'date', 'type']:
        if not file_data.get(key):
            print(f"Error: {file.name}")
            print(f"Details: YAML has no {key}.")
            sys.exit(1)
    if file_data['image'] and not file_data['image-alt']:
        print(f"Error: {file.name}")
        print(f"Details: YAML has an image but no image-alt description.")
        sys.exit(1)
    if file_data['type'] == 'short' and not (file_data.get('title') == file.name.rsplit('.', 1)[0] == file_data.get('date')):
        print(f"Error: {file.name}")
        print(f"Details: For short posts the file name, title, and date must match.")
        sys.exit(1)

def parse_location(loc_str):
    if not loc_str:
        return None
    lat, lon = map(float, loc_str.split(','))
    return {
        'latitude': lat,
        'longitude': lon
    } 

def create_version_data(content_data):
    uuid_count = Counter([item.get('uuid') for item in content_data])
    content_data.sort(key=lambda x: (x.get('uuid', ''), x['date']), reverse=True)
    current_uuid = None
    for item in content_data:
        item['versions'] = uuid_count[item.get('uuid')]
        if item.get('uuid') != current_uuid:
            item['latest'] = True
            current_uuid = item.get('uuid')
        else:
            item['latest'] = False

def correct_home_page_url(content_data):
    for item in content_data:
        if item['type'] == 'home':
            item['url'] = 'index'

def json_debug_dump(data):
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return super().default(obj)
    def dump_object_to_json(obj, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(obj, f, cls=DateTimeEncoder, ensure_ascii=False, indent=2)
        print(f"Created content_data.json for debugging.")
    dump_object_to_json(data, f"content_data.json")

def gather_content_data():
    content_data = []
    posts_directory = CONTENT_DIRECTORY / 'posts'
    for file in posts_directory.glob('**/*.md'):
        try:
            with open(file, 'r', encoding="utf-8") as f:
                file_string = f.read()
            yaml_part, markdown_part = file_string.split('---', 2)[1:]
            file_data = yaml.safe_load(yaml_part)
            verify_yaml_data(file, file_data)
            file_data['url'] = file.name.rsplit('.', 1)[0]
            file_data['title'] = typogrify(html.unescape(file_data.get('title') or file_data['url'].replace('-', ' ').title()))
            file_data['description'] = typogrify(html.unescape(file_data['description']))
            file_data['date'] = datetime.strptime(file_data['date'], '%Y-%m-%d-%H-%M-%S')
            file_data['location'] = parse_location(file_data.get('location'))
            file_data['html'] = typogrify(markdown.markdown(markdown_part))
            content_data.append(file_data)
        except Exception as e:
            print(f"Error: {file}")
            print(f"Details: {str(e)}.")
            sys.exit(1)
    create_version_data(content_data)
    correct_home_page_url(content_data)
    content_data.sort(key=lambda x: x['date'], reverse=True) # Final object must be sorted by date
    json_debug_dump(content_data) if parse_args().watch else None # Useful for testing; triggered along with watchdog
    return content_data

# Functions: Build pages

def remove_and_recreate_site_directory():
    shutil.rmtree(SITE_DIRECTORY, ignore_errors=True)
    os.makedirs(SITE_DIRECTORY)

def start_jinja2():
    templates_directory = BUILDER_DIRECTORY / 'templates'
    jinja_environment = Environment(loader=FileSystemLoader(templates_directory))
    template = jinja_environment.get_template('/boilerplate/base.html')
    return template

def prettify_html(html):
    formatter = bs4.formatter.HTMLFormatter(indent=4)
    soup = bs4.BeautifulSoup(html, "html.parser")
    return soup.prettify(formatter=formatter)

def build_pages(content_data):
    remove_and_recreate_site_directory() # Must happen before everything else! You've made this mistake before!
    template = start_jinja2()
    for page in content_data:
        output_html = template.render(
            content_template=f"{page['type']}.html", 
            page=page, posts=content_data, 
            now=datetime.now() # To automatically update the footer's year
            )
        prettify_html(output_html) # Nice but probably useless
        output_path = SITE_DIRECTORY / f"{page['url']}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_html)

# Functions: Move assets

def move_assets():
    # Images
    content_images_directory = CONTENT_DIRECTORY / 'images'
    site_images_directory = SITE_DIRECTORY / 'images'
    os.makedirs(site_images_directory, exist_ok=True)
    for image in content_images_directory.glob('*'):
        shutil.copy(image, site_images_directory)
    # CSS
    css_source_directory = BUILDER_DIRECTORY / 'css'
    css_output_directory = SITE_DIRECTORY / 'css'
    os.makedirs(css_output_directory, exist_ok=True)
    for css_file in css_source_directory.glob('*.css*'):
        if css_file.suffix in ['.css', '.map']:
            shutil.copy(css_file, css_output_directory)
    # Fonts
    fonts_source_directory = BUILDER_DIRECTORY / 'fonts'
    fonts_output_directory = SITE_DIRECTORY / 'fonts'
    os.makedirs(fonts_output_directory, exist_ok=True)
    for font in fonts_source_directory.glob('*'):
        shutil.copy(font, fonts_output_directory)
    # Assets
    assets_source_directory = BUILDER_DIRECTORY / 'assets'
    assets_output_directory = SITE_DIRECTORY / 'assets'
    os.makedirs(assets_output_directory, exist_ok=True)
    for asset in assets_source_directory.glob('*'):
        shutil.copy(asset, assets_output_directory)

# Functions: Other

def parse_args():
    parser = argparse.ArgumentParser(description='Circus Factions Builder')
    parser.add_argument('-w', '--watch', '--watchdog',
                        action='store_true',
                        help='Watch for changes and rebuild the site automatically')
    return parser.parse_args()

# Main

def main():
    start_time = time.time()
    update_content_files() # Must precede `gather_content_data()`. It changes content files!
    content_data = gather_content_data() # Any validation or transformation happens here.
    build_pages(content_data) # Annihilates the previous site directory.
    move_assets() # Everything other than HTML pages.
    elapsed_time = "{:.0f}".format((time.time() - start_time) * 1000)
    print(f"Done! Build Time: {elapsed_time} ms")
    if parse_args().watch:
        start_watching(BUILDER_DIRECTORY, CONTENT_DIRECTORY, [sys.argv[0]] + sys.argv[1:])

if __name__ == '__main__':
    main() #