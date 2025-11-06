from urllib.parse import urlparse
from dotenv import load_dotenv
import bs4
import requests
import os
from requests.exceptions import TooManyRedirects, RequestException
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path
import re
import logging
from datetime import datetime

current_time = datetime.now()
log_filename = current_time.strftime("%Y_%m_%d_%H_%M_%S")

logger = logging.getLogger(__name__)


# restAPI settings
# example new_site_api_url = 'https://hebrew-academy.org.il/wp-json/wp/v2/posts'
# example old_site_api_url = 'https://old.hebrew-academy.org.il/wp-json/wp/v2/posts'
header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Encoding': 'identity'
}
# auth
load_dotenv()
basic = HTTPBasicAuth('danby',os.getenv("basic_key"))
oldbasic = HTTPBasicAuth('danby',os.getenv("oldbasic_key")) 

# list of all posts in the new site with bad shortcodes
## the txt file that contain all the urls for the posts.
def create_api_list(import_file_path):
    new_site_posts_file = Path(import_file_path)
    new_site_posts_string = new_site_posts_file.read_text()
    new_site_posts_urls = new_site_posts_string.split('\n')

    # extracting the restAPI json endpoint for each post url
    ## parameter: txt file with all the links, seperated by \n
    ## returns a list with all the restAPI links
    new_site_posts_apis = []
        
    for url in new_site_posts_urls:
        try:
            extract_post = requests.get(url,headers=header,allow_redirects=True)
            extract_post.raise_for_status()
            post_soup = bs4.BeautifulSoup(extract_post.text,'html.parser')
            type(post_soup)
            api_link = post_soup.find('link', href=lambda x: x and "http://hebrewacademy.local/wp-json/wp" in x)
            if api_link:
                href_url = api_link.get('href')
                new_site_posts_apis.append(href_url)
        except TooManyRedirects:
            logger.exception(f"Too many redirects for {url} - skipping")
            continue  # Skip to next URL
        
        except RequestException as e:
            logger.exception(f"Request failed for {url}, Exception: {e}")
            continue  # Skip to next URL
            
        except Exception as e:
            logger.exception(f"Other error for {url}: {e}")
            continue  # Skip to next URL
    url_lists = [new_site_posts_apis,new_site_posts_urls]
    return url_lists


# get new post json
## get request with admin permissions to get raw data (not rendered)
def get_new_post_json(new_api_url):
    admin_r = requests.get(new_api_url + '?context=edit',headers=header, auth=basic)
    admin_r.raise_for_status()
    json_get = admin_r.json()
    new_post_content = (json_get['content']['raw'])
    ## extracting the slideshow shortcode from post content
    shortcode_pattern = re.compile(r"(\[slideshow_deploy id='(\d+)'\])")
    shortcode_search = shortcode_pattern.search(new_post_content)
    if shortcode_search:
        old_shortcode = shortcode_search.group(2)
    else:
        raise ValueError("No slidshow shortcode found in post")
        
    new_post_info = [old_shortcode,new_post_content]
    return new_post_info


def extract_images(old_shortcode):
    old_slideshow_api = f'https://old.hebrew-academy.org.il/wp-json/slideshow/v1/slideshows/{old_shortcode}'
    api_extract_r = requests.get(old_slideshow_api ,headers=header, auth=oldbasic)
    api_extract_r.raise_for_status()
    json_extract = api_extract_r.json()
    old_slideshows_title = json_extract['title']
    slides_list = json_extract['slides']
    old_slideshow_info = [old_slideshows_title,slides_list]
    
    return old_slideshow_info

def download_images(slides_list,old_slideshow_title):
    # create a folder based on slideshow name
    try:
        parent_folder = os.getcwd()
        folder_path = os.path.join(parent_folder,old_slideshow_title)
        os.mkdir(folder_path)
        logger.info(f"Directory '{old_slideshow_title}' created successfully.")
    except FileExistsError:
        logger.exception(f"Directory '{old_slideshow_title}' already exists.")
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
    # for each slide download the image to the folder, add path to dictionary
    for slide in slides_list:
        image_url = slide['image_url']
        parsed_url = urlparse(image_url)
        try:
            images_req = requests.get(image_url,headers=header,allow_redirects=True)
            images_req.raise_for_status()
        except Exception as e:
            logger.exception(f'didnt download image {image_url} ,Exception:{e}')
            continue
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            filename = f"image_{hash(image_url)}.jpg"
        file_path = os.path.join(folder_path, filename)
        with open(file_path,'wb') as image_file:
            for chunk in images_req.iter_content(chunk_size=8129):
                if chunk:
                    image_file.write(chunk)
        logger.info(f"Downloaded: {filename}")
        # add file path to dictionary
        slide['file_path'] = file_path
    return slides_list

def upload_slide_images(slides_list,media_api):
    for slide in slides_list:
        try:
            file_open = open(slide['file_path'],'rb')
        except Exception as e:
            logger.exception(f'couldnt open file {slide['file_path']}, Exception: {e}')
            continue
        upload_data = {
            'type' : slide['type'],
            'file' : file_open,
            'file_name' : os.path.basename(slide['file_path']),
            'title' : slide['title'],
            'description' : slide['description']
        }
        try:
            upload_slide_r = requests.post(media_api,headers=header,auth = basic,files = upload_data)
            upload_slide_r.raise_for_status()
        except Exception as e:
            logger.exception(f'couldnt upload file {slide['file_path']}, Exception: {e}')
            continue
            
        upload_slide_json = upload_slide_r.json()
        new_image_id = upload_slide_json['id']
        slide['id'] = new_image_id
    return slides_list

    
def create_slideshow_post(old_slideshow_title):
    new_slideshows_api = 'http://hebrewacademy.local/wp-json/wp/v2/slideshow/'
    new_slideshow_json = {
        'title' : old_slideshow_title,
        'type' : 'slideshow',
        'status' : 'publish',
        'content' : ''
    }
    create_slideshow_post_r = requests.post(new_slideshows_api,headers=header,json=new_slideshow_json, auth=basic)
    create_slideshow_post_r.raise_for_status()
    created_slideshow_json = create_slideshow_post_r.json()
    new_slideshow_title = created_slideshow_json['title']
    new_slideshow_id = created_slideshow_json['id']
    logger.info(f"Successfully created the slideshow: {new_slideshow_title} with ID: {new_slideshow_id}")
    return new_slideshow_id

def edit_slideshow_post_meta(new_slideshow_id,slides_list):
    slideshow_translated_items = []
    for slide in slides_list:
        slideshow_translated_items.append({
            "type" : "image",
            "title" : slide['title'],
            "description" : slide['description'],
            "url" : "",
            "image_id" : slide['id'],
            "alt" : slide['image_alt']
        })
    custom_api = f'http://hebrewacademy.local/wp-json/custom/v1/slideshow/{new_slideshow_id}/items'
    metadata_payload = {
        'slideshow_items': slideshow_translated_items
    }
    edit_meta_r = requests.post(custom_api,headers=header,auth=basic,json=metadata_payload)
    edit_meta_r.raise_for_status()
    edit_meta_json = edit_meta_r.json()
    logger.info(f"Successfully edited the slideshow")
    return edit_meta_json
## 
def edit_shortcodes(new_post_api,new_slideshow_id,new_post_content):
    # edit the content: find the embed shortcode and change it to the new shortcode
    new_shortcode = f"[slideshow id=\"{new_slideshow_id}\"]"
    old_shortcode_re = re.compile(r"(\[slideshow_deploy id='(\d+)'\])")
    edited_content = old_shortcode_re.sub(new_shortcode,new_post_content)
    r_edit_shortcode = requests.put(new_post_api + '?context=edit' ,headers=header,auth=basic, json={'content': {'raw': edited_content}})
    r_edit_shortcode.raise_for_status()
    logger.info(f"Successfully edited the Shortcode")
    
    return new_shortcode
    
    