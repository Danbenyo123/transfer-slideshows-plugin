# WordPress Slideshow Migration Tool

A Python-based automation tool for migrating slideshows from an old WordPress site to a new WordPress site. The tool extracts slideshow content, downloads images, uploads them to the new site, creates new slideshow posts, and updates shortcodes in existing posts.

## Overview

This tool automates the process of transferring slideshows between WordPress installations by:
- Reading a list of post URLs from a text file
- Extracting old slideshow shortcodes from post content
- Downloading slideshow images from the old site
- Uploading images to the new site's media library
- Creating new slideshow posts with proper metadata
- Updating post content with new slideshow shortcodes

## Features

- **Batch Processing**: Handles multiple posts in a single run
- **Error Handling**: Continues processing even if individual posts fail
- **Detailed Logging**: Comprehensive logging with color-coded console output and file logging
- **Progress Tracking**: Tracks successful and failed migrations
- **Image Management**: Automatically downloads and uploads slideshow images
- **Metadata Preservation**: Maintains image titles, descriptions, and alt text

## Requirements

- Python 3.6+
- WordPress REST API access on both old and new sites
- Authentication credentials for both WordPress installations

### Python Dependencies

```
requests
python-dotenv
beautifulsoup4
colorlog
```

## Installation

1. Clone or download the repository

2. Install required packages:
```bash
pip install requests python-dotenv beautifulsoup4 colorlog
```

3. Create a `.env` file in the project root with your credentials:
```env
basic_key=YOUR_NEW_SITE_PASSWORD
oldbasic_key=YOUR_OLD_SITE_PASSWORD
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

- `basic_key`: Password for authentication on the new WordPress site
- `oldbasic_key`: Password for authentication on the old WordPress site

### Input File

Create a text file (default: `corrected_urls_testing_left.txt`) containing URLs of posts to process, one per line:

```
https://hebrew-academy.org.il/post-1/
https://hebrew-academy.org.il/post-2/
https://hebrew-academy.org.il/post-3/
```

### Site URLs

Update the following URLs in the code to match your WordPress installations:

**In `functions.py`:**
- Old site API: `https://old.hebrew-academy.org.il/wp-json/`
- New site API: `http://hebrewacademy.local/wp-json/`

**In `workflow.py`:**
- Media API: `http://hebrewacademy.local/wp-json/wp/v2/media`

## Usage

### Basic Usage

```bash
python workflow.py
```

### File Structure

```
project/
├── workflow.py              # Main execution script
├── functions.py            # Utility functions
├── .env                    # Environment variables (credentials)
├── corrected_urls_testing_left.txt  # Input file with post URLs
├── YYYY_MM_DD_HH_MM_SS.log # Log file (auto-generated)
└── [slideshow folders]/    # Downloaded images (auto-generated)
```

## How It Works

### Workflow Steps

1. **Load URLs**: Reads post URLs from input text file
2. **Extract API Endpoints**: Converts post URLs to REST API endpoints
3. **For Each Post**:
   - Fetch post content via REST API
   - Extract old slideshow shortcode ID
   - Retrieve slideshow data from old site API
   - Download all slideshow images to local folder
   - Upload images to new site's media library
   - Create new slideshow post
   - Update slideshow metadata with image IDs
   - Replace old shortcode with new shortcode in post content
4. **Generate Report**: Lists successful and failed migrations

### API Endpoints Used

**Old Site:**
- `/wp-json/slideshow/v1/slideshows/{id}` - Retrieve slideshow data

**New Site:**
- `/wp-json/wp/v2/posts/{id}` - Get/update post content
- `/wp-json/wp/v2/media` - Upload images
- `/wp-json/wp/v2/slideshow/` - Create slideshow posts
- `/wp-json/custom/v1/slideshow/{id}/items` - Update slideshow metadata

## Logging

The tool generates two types of logs:

### Console Logging
Color-coded output showing real-time progress:
- **Blue**: Informational messages
- **Yellow**: Warnings
- **Red**: Errors
- **Cyan**: Debug information

### File Logging
Detailed logs saved to `YYYY_MM_DD_HH_MM_SS.log` with:
- Timestamps
- Log levels
- Detailed error messages with stack traces
- URLs processed
- Success/failure status

## Error Handling

The tool includes robust error handling:

- **Network Errors**: Retries and continues with next post
- **Missing Shortcodes**: Skips posts without slideshow shortcodes
- **Download Failures**: Logs error and continues with next image
- **Upload Failures**: Logs error and continues with next slide
- **API Errors**: Catches and logs HTTP errors

## Output

### Success Report

At the end of execution, the tool outputs:
- Total number of posts processed successfully
- List of successful post URLs
- Total number of failed posts
- List of failed post URLs

### Generated Folders

For each slideshow, a folder is created containing downloaded images:
```
[Slideshow Title]/
├── image1.jpg
├── image2.png
└── image3.jpg
```

## Troubleshooting

### Common Issues

**Authentication Errors**
- Verify credentials in `.env` file
- Ensure WordPress user has proper permissions
- Check if Application Passwords are enabled in WordPress

**API Endpoint Not Found**
- Verify WordPress REST API is enabled
- Check custom API endpoints are registered
- Ensure slideshow plugin is installed on both sites

**Too Many Redirects**
- Check URL format (trailing slashes)
- Verify site is accessible
- Check for redirect loops in WordPress

**Permission Errors**
- Ensure user has `edit_posts` capability
- Verify user can upload media files
- Check custom post type permissions

**Missing Shortcodes**
- Verify post contains `[slideshow_deploy id='X']` format
- Check regex pattern matches shortcode format

## Security Considerations

- **Never commit `.env` file** to version control
- Store credentials securely
- Use WordPress Application Passwords instead of main passwords
- Limit API user permissions to minimum required
- Run on secure network when transferring content

## Limitations

- Requires custom slideshow API endpoint on old site
- Assumes specific shortcode format: `[slideshow_deploy id='X']`
- Creates new slideshow ID (doesn't preserve original IDs)
- Requires manual setup of `.env` and input file

## Future Enhancements

- [ ] Add command-line arguments for input file and URLs
- [ ] Support for additional shortcode formats
- [ ] Parallel processing for faster execution
- [ ] Resume capability for interrupted runs
- [ ] Dry-run mode to preview changes
- [ ] Image optimization during transfer
- [ ] Support for other media types (videos, PDFs)

## License

[Add your license information here]

## Authors

[Add author information here]

## Support

For issues or questions:
- Check log files for detailed error messages
- Verify WordPress REST API is accessible
- Ensure all dependencies are installed
- Review authentication credentials

---

**Note**: This tool is designed for migrating Hebrew Academy WordPress sites. Modify URLs and API endpoints for your specific use case.
