#!/usr/bin/env python3

import time
import markdown
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import yaml
import re
from datetime import datetime
from typogrify.filters import typogrify
import os
import shutil
from modules.watchdog import start_watching
from collections import Counter
import sys
import json

# Record the script's start time.
start_time = time.time()

# Configurations.
build_directory = Path('~/GitHub/circus-factions-builder').expanduser() # "expanduser" is necessary for this to work on both Mac and Ubuntu.
content_directory = Path('~/GitHub/circus-factions-content').expanduser()
output_directory = Path('~/GitHub/circus-factions-site/public').expanduser()
watchdog = False

# Process the Markdown files.

## Create an empty markdown_data list.
markdown_data = []

## Extract data from the Markdown files in the content directory.
markdown_directory = content_directory / 'markdown'
for file in markdown_directory.glob('**/*.md'):
    try:
        with open(file, 'r', encoding="utf-8") as f:
            file_string = f.read()
        ### Split each file into YAML and Markdown parts.
        yaml_part, markdown_part = file_string.split('---', 2)[1:]
        ### Load the YAML into the file_data dictionary.
        file_data = yaml.safe_load(yaml_part)
        ### Add the file name to the file_data dictionary.
        file_data['file-name'] = file.name.rsplit('.', 1)[0]
        ### Extract the date-time from the file name.
        date_time_match = re.match(r'(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})', file.name)
        ### Convert the match object to a string.
        date_time_str = date_time_match.group(1)
        ### Convert the date-time string to a datetime object.
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d-%H-%M-%S')
        ### Add the datetime object to the file_data dictionary.
        file_data['date-time'] = date_time_obj
        ### Establish the page URL.
        #### Remove `.md` from the file name.
        ##file_name_without_extension = file.name.rsplit('.', 1)[0]
        #### Figure out if there's more than just a time stamp in the file name.
        file_name_parts = file_data['file-name'].split('-', 6)
        #### If there's more than the time stamp, use that stuff. Otherwise use the time stamp.
        if len(file_name_parts) > 6:
            url = '-'.join(file_name_parts[6:])
        else:
            url = file_data['file-name']
        #### Add the URL to the file_data dictionary.
        file_data['url'] = url
        ### Convert the Markdown to HTML.
        html = markdown.markdown(markdown_part)
        ### Fix typographic issues in the HTML with Typogrify.
        html = typogrify(html)
        ### Add the HTML to the file_data dictionary.
        file_data['html'] = html
        ### Add the file_data dictionary to the markdown_data list.
        markdown_data.append(file_data)
    except Exception as e:
        print(f"Error gathering data from this Markdown file:")
        print(f"{file}")
        print(f"Details: {str(e)}.")
        sys.exit(1)

# Add version metadata to each post.
uuid_count = Counter([item.get('uuid') for item in markdown_data])
markdown_data.sort(key=lambda x: (x.get('uuid', ''), x['date-time']), reverse=True)
for item in markdown_data:
    item['versions'] = uuid_count[item.get('uuid')]
current_uuid = None
for item in markdown_data:
    item['versions'] = uuid_count[item.get('uuid')]
    if item.get('uuid') != current_uuid:
        item['latest'] = True
        current_uuid = item.get('uuid')
    else:
        item['latest'] = False

# # TESTING PURPOSES ONLY
# # DUMP THE MARKDOWN DATA TO A FILE
# class DateTimeEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, datetime):
#             return obj.isoformat()
#         return super().default(obj)
# def dump_object_to_json(obj, filename):
#     with open(filename, 'w', encoding='utf-8') as f:
#         json.dump(obj, f, cls=DateTimeEncoder, ensure_ascii=False, indent=2)
#     print(f"Successfully wrote JSON to {filename}")
# my_object = markdown_data
# dump_object_to_json(my_object, build_directory / "output.json")

# Start Jinja environment.
templates_directory = build_directory / 'templates'
jinja_environment = Environment(loader=FileSystemLoader(templates_directory))
template = jinja_environment.get_template('/essentials/base.html')

# Before you actually build any output files, remove and recreate the output directory.

# Remove and recreate the output directory.
shutil.rmtree(output_directory)
os.makedirs(output_directory)

# Build the home page (currently a summary version of all "long" posts, in reverse chronological order).

## Isolate the home page's own data from markdown_data.
home_markdown_data = next((item for item in markdown_data if item.get('type') == 'home'), None)
## Isolate the posts you want to show on the home page.
home_page_posts = [item for item in markdown_data if item.get('type') in ['long', 'essay']]
## Sort the long_posts_data list in reverse chronological order.
home_page_posts.sort(key=lambda x: x['date-time'], reverse=True)
## Pass the home_data and long_posts_data to Jinja to generate the home page HTML.
output_html = template.render(content_template='home.html', home_markdown_data=home_markdown_data, home_page_posts=home_page_posts)
## Establish the output path for the home page.
output_path = Path(output_directory / 'index.html')
## Write the home page HTML to the output directory.
with open(output_path, 'w', encoding="utf-8") as f:
    f.write(output_html)

# Build essay pages.

## First build essay pages for the latest version of each essay.

## Isolate the essays from markdown_data.
essays = [item for item in markdown_data if (item.get('type') == 'essay' and item.get('latest') == True)]
## Iterate through the list to generate the output HTML for each essay.
for essay in essays:
    ## Pass the essay data to Jinja2 to generate the essay's HTML page.
    output_html = template.render(content_template='posts/essay.html', essay=essay)
    ## Establish the output path for the essay's HTML page.
    output_path = Path(output_directory / essay['url'] / f"index.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ## Write the essay's HTML page to the output directory.
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write(output_html)

## Next build essay pages for older versions of each essay.

## Isolate deprecated essays from markdown_data.
deprecated_essays = [item for item in markdown_data if (item.get('type') == 'essay' and item.get('latest') == False)]
## Iterate through the list to generate the output HTML for each essay.
for essay in deprecated_essays:
    ## Pass the essay data to Jinja2 to generate the essay's HTML page.
    output_html = template.render(content_template='posts/deprecated_essay.html', essay=essay)
    ## Establish the output path for the essay's HTML page.
    output_path = Path(output_directory / essay['url'] / f"{essay['file-name']}.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ## Write the essay's HTML page to the output directory.
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write(output_html)

## Next build the "versions" page for each essay that needs one.
latest_essays_with_versions = [item for item in markdown_data if (item.get('type') == 'essay' and item.get('latest') == True and item.get('versions') > 1)]
deprecated_essays = [item for item in markdown_data if (item.get('type') == 'essay' and item.get('latest') == False)]
#deprecated_essays.sort(key=lambda x: x['date-time'], reverse=True)
for essay in latest_essays_with_versions:
    ## Isolate the deprecated versions of the essay.
    # print(f"Current essay UUID: {essay.get('uuid')}")
    # print(f"Deprecated essays UUIDs: {[item.get('uuid') for item in deprecated_essays]}")
    deprecated_versions = [item for item in deprecated_essays if item.get('uuid') == essay.get('uuid')]
    ## Pass the essay data to Jinja2 to generate the essay's HTML page.
    output_html = template.render(content_template='posts/versions.html', essay=essay, deprecated_versions=deprecated_versions)
    ## Establish the output path for the essay's HTML page.
    output_path = Path(output_directory / essay['url'] / f"versions.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ## Write the essay's HTML page to the output directory.
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write(output_html)

# # Build pages for long posts.

# ## Isolate the long posts from markdown_data.
# long_posts = [item for item in markdown_data if item.get('type') == 'long']
# ## Iterate through long_posts to generate the output HTML for each post.
# for post in long_posts:
#     ## Pass the post data to Jinja to generate the post page HTML.
#     output_html = template.render(content_template='long_post.html', post=post)
#     ## Establish the output path for the post page.
#     output_path = Path(output_directory / f"{post['url']}.html")
#     ## Write the post page HTML to the output directory.
#     with open(output_path, 'w', encoding="utf-8") as f:
#         f.write(output_html)

# Build feed page.

## Isolate the feed page's own data from markdown_data.
feed_markdown_data = next((item for item in markdown_data if item.get('type') == 'feed'), None)
## Isolate the posts you want to show on the feed page.
feed_page_posts = [item for item in markdown_data if item.get('type') in ['long', 'short']]
## Sort the feed_posts list in reverse chronological order.
feed_page_posts.sort(key=lambda x: x['date-time'], reverse=True)
## Pass the feed_data and feed_posts to Jinja to generate the feed page HTML.
output_html = template.render(content_template='feed.html', feed_markdown_data=feed_markdown_data, feed_page_posts=feed_page_posts)
## Establish the output path for the feed page.
output_path = Path(output_directory / 'feed.html')
## Write the feed page HTML to the output directory.
with open(output_path, 'w', encoding="utf-8") as f:
    f.write(output_html)

# Build pages for short posts.

## Isolate the short posts from markdown_data.
short_posts = [item for item in markdown_data if item.get('type') == 'short']
## Iterate through short_posts to generate the output HTML for each post.
for post in short_posts:
    ## Pass the post data to Jinja to generate the post page HTML.
    output_html = template.render(content_template='short_post.html', post=post)
    ## Establish the output path for the post page.
    output_path = Path(output_directory / f"{post['url']}.html")
    ## Write the post page HTML to the output directory.
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write(output_html)

# Move all images to the output directory.
images_source_directory = content_directory / 'images'
images_output_directory = output_directory / 'images'
os.makedirs(images_output_directory, exist_ok=True)
for image in images_source_directory.glob('*'):
    shutil.copy(image, images_output_directory)

## Move all CSS files to the output directory.
css_source_directory = build_directory / 'css'
css_output_directory = output_directory / 'css'
os.makedirs(css_output_directory, exist_ok=True)
for css_file in css_source_directory.glob('*.css*'):
    if css_file.suffix in ['.css', '.map']:
        shutil.copy(css_file, css_output_directory)

## Move all fonts to the output directory.
fonts_source_directory = build_directory / 'fonts'
fonts_output_directory = output_directory / 'fonts'
os.makedirs(fonts_output_directory, exist_ok=True)
for font in fonts_source_directory.glob('*'):
    shutil.copy(font, fonts_output_directory)

# Finish up.

# Print the script's run time.
elapsed_time = "{:.0f}".format((time.time() - start_time) * 1000)
print(f"Done! Build Time: {elapsed_time} ms")

# If Watchdog is active, watch for changes and automatically rebuild.
start_watching(build_directory, content_directory) if watchdog else None

