#!/usr/bin/env python3

"""
(Are you again wondering about the first line? It's a "shebang". It's necessary for running this script with a simple `build.py` instead of `python3 build.py`. And yes, it needs to come before any comments. And you can't put inline comments after it. Hence this comment.)

WELCOME TO THE BUILD SCRIPT FOR CIRCUS FACTIONS!

If you're reading this you've probably forgotten how your website works. Here's the good news: Everything you need to know is right here in this script! Here's the bad news: This script has about twenty lines of comments for every line of code. Deal with it!

If you're reading this and you're not me (Phillip Miller), you're probably thinking "wow, this guy isn't much of a programmer". You're right! Nothing you find below will be efficient, elegant, or exemplary. None of that matters to me. This script has only two jobs: (1) it needs to work, and (2) it needs to be easy for me to understand and maintain after months or years of neglect.

CONTENTS (each section is styled below as a Markdown heading)
- Before anything else, remind me of everything I need to know about Circus Factions
- Walk me through this whole repository
- Now let's dig into the script itself
    - Historical notes
    - Basic principles
    - Import statements
    - Configurations




This script is presented as a Markdown document, so each major section  is a Markdown document,

- Circus Factions Fundamentals


# 
# How Circus Factions works

Before we get into the script, let's summarize how *everything* works.

The site relies on three GitHub repositories:
- `circus-factions-content`: Holds all of the site's source material -- mostly Markdown files and images.
- `circus-factions-builder`: Holds everything needed to turn the source material into the final site assets (including this script).
- `circus-factions-site`: Holds the final site assets.

Why three repositories? Why not combine "content" and "builder"? Why bother with "site" rather than just deploying the assets as part of the build script?
- I like having the option to keep "content" private while "builder" is public, especially given that "content" often contains unfinished writing.
- I like being able to use Obsidian, across all of my devices, to manage everything in "content". This would be trickier (but not impossible) if "content" were combined with "builder".




 A separate content repository makes it easier to (1) keep it private if I so choose, especially for the sake of work-in-progress stuff, and (2) use Obsidian to create, edit, and organize my Markdown files.


## Basic principles for this script

This script should be a one-stop-shop. All other files in this repository will be clearly referenced and explained within this script. Even the README just points to this script. If I fail to keep this script's comments up to date I should hang my head in shame and go without ice cream for an entire year.

This script is organized like a Markdown document. It is extremely linear. Just follow it step by step. You'll rarely need to inspect modules or functions. You'll never need to worry about asynchronous/parallel operations.

## Historical notes that might prevent me from repeating stupid mistakes

When I first created this program it was designed to be a general-purpose static website generator. It could service any number of sites via configuration files and command line flags. It totally worked and was totally ridiculous. Why? First: It added a huge amount of complexity in order to save me from simply copying and pasting a few bits of simple code into new build scripts. Second: I couldn't add any feature to a given site without first worrying about how to fully incorporate that feature into the general-purpose builder. Third: At the time I didn't even have any other websites! Fourth: It's not like anyone else is going to use this thing.

When I first created this program I also designed it to handle incremental builds. It seemed so wasteful to rebuild the whole site whenever a post was added or changed. This also totally worked and was also totally ridiculous. Why? Essentially the same reasons as the previous mistake. First: It added a huge amount of complexity to solve a problem that didn't really exist. Computation is essentially free at my scale, and a bit of testing confirmed that any modern machine could rebuild my site in seconds even if it contained thousands of posts and images. Second: I quickly realized that new features could dramatically complicate the incremental builds (I knew I'd gone too far when I found myself researching "dependency graphs"). The program can be so much simpler if you just totally rebuild the site every time it runs.

Given the complexity introduced by the two mistakes described above, even after "fixing" those mistakes I had a program that was split into many different modules and functions. When I came back to the code after neglecting it for a couple months I found myself struggling to remember how it all fit together. I eventually accepted that this program is not especially complicated, that no one is holding me to professional programming standards, and that it would be easier for me to maintain the program if it were a single script that happens to be rather long, extremely linear, and heavily commented. So here we are.

## A reminder about the structure of Circus Factions

Before we even get into 

This website very intentionally depends on three repositories.


"""


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
from PIL import Image
import glob
import json

# An Emerging Outline of What this Script Actually Does
# 1. Process Images. Do this *first* because you want to permanently alter the original data in the content directory, so you don't have to do it again later.
# 2. Gather all of the data from the Markdown files.
# 3. Build the batch-type pages, like all the essay pages, fragment pages, image pages, and so on. You need to build these anyway no matter what.
# 4. Build the pages that are a bit more custom, like the home page and other aggregate pages.



# Record the script's start time to easily measure how long the build takes.
start_time = time.time()

# Configurations.
build_directory = Path('~/GitHub/circus-factions-builder').expanduser() # "expanduser" is necessary for this to work on both Mac and Ubuntu.
content_directory = Path('~/GitHub/circus-factions-content').expanduser()
output_directory = Path('~/GitHub/circus-factions-site/public').expanduser()
watchdog = False

# Process Images.
# Convert all images in the content directory to WebP format.
# Update Markdown files in the content directory to reflect the new image paths.

image_directory = content_directory / 'images'
image_files = glob.glob(os.path.join(image_directory, "*.[jpJ][pnP][egEG]*"))
for image_file in image_files:
    file_name = os.path.splitext(os.path.basename(image_file))[0]
    # Open the image
    img = Image.open(image_file)
    # Convert and save as WebP
    webp_path = os.path.join(image_directory, f"{file_name}.webp")
    img.save(webp_path, format="WebP", quality=80)

# Update Markdown files to reflect the new image paths.
for file in content_directory.glob('**/*.md'):
    with open(file, 'r', encoding="utf-8") as f:
        file_string = f.read()
    file_string = file_string.replace('.jpg', '.webp')
    file_string = file_string.replace('.jpeg', '.webp')
    file_string = file_string.replace('.png', '.webp')
    with open(file, 'w', encoding="utf-8") as f:
        f.write(file_string)

# Delete JPG, JPEG, and PNG files in the content directory.
image_files = glob.glob(os.path.join(image_directory, "*.[jpJ][pnP][egEG]*"))
for image_file in image_files:
    os.remove(image_file)


# MARKDOWN DATA.
# Create a new list that gathers and transforms data from Markdown files.

## Create an empty list called `markdown_data`. This will hold the final data.
markdown_data = []

## Extract data from Markdown files in the content directory.
markdown_directory = content_directory / 'publish' # Any Markdown file that's ready to publish lives in this folder.
for file in markdown_directory.glob('**/*.md'): # I only want Markdown files. Anything else that sneaks in should be ignored.
    try: # Using a "try" block makes it easier to report which file caused an error without lots of complex error handling.
        with open(file, 'r', encoding="utf-8") as f:
            file_string = f.read()
        ### Split each file into YAML and Markdown parts.
        yaml_part, markdown_part = file_string.split('---', 2)[1:]
        ### Load the YAML into the file_data dictionary.
        file_data = yaml.safe_load(yaml_part)
        ### Add the file name to the file_data dictionary.
        file_data['file-name'] = file.name.rsplit('.', 1)[0] # Remove the file extension.
        ### Extract the date-time from the file name.
        date_time_match = re.match(r'(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})', file.name)
        ### Convert the match object to a string.
        date_time_str = date_time_match.group(1)
        ### Convert the date-time string to a datetime object.
        date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d-%H-%M-%S')
        ### Add the datetime object to the file_data dictionary.
        file_data['date-time'] = date_time_obj
        ### Establish a page URL. "Fragments" will only have a date-time stamp. Other items should have additional parts in the URL.
        #### Figure out if there's more than just a time stamp in the file name.
        file_name_parts = file_data['file-name'].split('-', 6)
        #### If there's more than the time stamp, use that stuff. Otherwise use the time stamp.
        if len(file_name_parts) > 6:
            file_data['url'] = '-'.join(file_name_parts[6:]) # This could become a problem in the future if I run into issues with duplicate URLs.
        else:
            file_data['url'] = file_data['file-name']
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

