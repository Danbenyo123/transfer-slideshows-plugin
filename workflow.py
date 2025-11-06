import functions
import sys
from dotenv import load_dotenv
import os
import bs4
import requests
from requests.exceptions import TooManyRedirects, RequestException
from requests.auth import HTTPBasicAuth
import json
from pathlib import Path
import re
import logging
from datetime import datetime
import colorlog

console_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt='%H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

# time
current_time = datetime.now()
log_filename = current_time.strftime("%Y_%m_%d_%H_%M_%S")


logging.basicConfig(level=logging.INFO,filename =f"{log_filename}.log",filemode="w"
                    ,format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)



header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Encoding': 'identity'
}
# auth
load_dotenv()
basic = HTTPBasicAuth('danby',os.getenv("basic_key"))
oldbasic = HTTPBasicAuth('danby',os.getenv("oldbasic_key"))

# get the list of new posts urls with old slideshows urls from file
success_posts = []
try:
    logging.info(f"creating api list")
    new_site_url_list = functions.create_api_list('./corrected_urls_testing_left.txt')
    new_site_url_posts = new_site_url_list[1].copy()
    logging.info(f'URL List: {new_site_url_posts}')
    new_site_api_list = new_site_url_list[0].copy()
    logging.info(f'API List: {new_site_api_list}')
except Exception as e:
    logging.error(f"Failed to create the api list")
    
    
# batch transfer slideshows for all posts in list
for i, new_api_url in enumerate(new_site_api_list):
    try:
        logging.info(f"Processing {new_api_url}")
        url_post = new_site_url_posts[i]
        # get new post json
        new_post_json = functions.get_new_post_json(new_api_url)
        ## getting the old shortcode
        old_shortcode = new_post_json[0]
        logging.info(f"old shortcode is {old_shortcode}")
        ## getting the new post content
        new_post_content = new_post_json[1]
        
        
        # using old shortcode to extract old slideshow: title images and descriptions
        
        try:
            logging.info("Extracting Images...")
            old_slideshow_info = functions.extract_images(old_shortcode)
            old_slideshow_title = old_slideshow_info[0]
            slides_list = old_slideshow_info[1]
        except ValueError as e:
            logging.warning(f"Skipping {url_post}: {e}")
            continue  # Skip to next post
        
        except Exception as e:
            logging.exception(f"Failed to extract info from slideshow (id): {old_shortcode}, Exception: {e}")
            continue
        else:
            logging.info(f"Extracting successfull")
        # downloading images
        try:
            logging.info("Downloading Images...")
            slides_list = functions.download_images(slides_list,old_slideshow_title)
        except Exception as e:
            logging.exception(f"Failed to download slide: {old_slideshow_title} ,Exception: {e}")
            continue
        else:
            logging.info(f"Slideshow {old_slideshow_title} download succesfull!")
        # upload images to new site media
        ## media api url
        media_api = 'http://hebrewacademy.local/wp-json/wp/v2/media'
        try:
            logging.info("Uploading Slides...")
            slides_list = functions.upload_slide_images(slides_list,media_api)
        except Exception as e:
            logging.exception(f"Failed to upload slideshow: {old_slideshow_title} ,Exception: {e}")
            print(f'Upload failed, beacuse of {e}')
            continue
            
        else:
            logging.info(f"Slideshow {old_slideshow_title} upload succesfull!")

        
        # create new slideshow post
        try:
            logging.info("Creating new Slideshow post...")
            new_slideshow_id = functions.create_slideshow_post(old_slideshow_title)
        except Exception as e:
            logging.exception(f"Couldnt create slideshow: {old_slideshow_title} Exception: {e}")
        else:
            logging.info(f"Slideshow {old_slideshow_title} created")
    # !! need to ask aviv to give permission for slideshow api, currently not working.
    # edit the slide show meta to insert slides
        try:
            logging.info(f"editing Slideshow metadata for {old_slideshow_title}...")
            functions.edit_slideshow_post_meta(new_slideshow_id,slides_list)
        except Exception as e:
            logging.exception(f"failed editing metadata, Exception: {e}")
            
        else:
            logging.info(f"Slideshow {old_slideshow_title} metadata edited")
    # edit the shortcodes
        try:
            logging.info(f"Editing shortcode for {new_api_url} ...")
            functions.edit_shortcodes(new_api_url,new_slideshow_id,new_post_content)
        except Exception as e:
            logging.exception(f"Couldnt edit shortcode, Exception: {e}")
        else:
            logging.info(f"Old shortcode replaced with new one.")
        success_posts.append(url_post)
        
    except Exception as e:
        logging.warning(f"Failed to process {new_api_url} : {e}", exc_info=True)
        continue
    
not_finishied_urls = [x for x in new_site_url_posts if x not in success_posts]
logging.info(f"""
                Finished {len(success_posts)} of Total posts ({len(new_site_url_posts)}):
                {success_posts}
                Not finished posts ({len(not_finishied_urls)}):
                {not_finishied_urls}
                """)
