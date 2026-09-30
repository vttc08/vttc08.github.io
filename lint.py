import logging
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import frontmatter
import yaml

from logging_config import configure_logging

configure_logging()

logger = logging.getLogger(__name__)


def _count_words_in_markdown(markdown):
    text = markdown

    # Comments
    text = re.sub(r'<!--(.*?)-->', '', text, flags=re.MULTILINE)
    # Tabs to spaces
    text = text.replace('\t', '    ')
    # More than 1 space to 4 spaces
    text = re.sub(r'[ ]{2,}', '    ', text)
    # Footnotes
    text = re.sub(r'^\[[^]]*\][^(].*', '', text, flags=re.MULTILINE)
    # Indented blocks of code
    text = re.sub(r'^( {4,}[^-*]).*', '', text, flags=re.MULTILINE)
    # Custom header IDs
    text = re.sub(r'{#.*}', '', text)
    # Replace newlines with spaces for uniform handling
    text = text.replace('\n', ' ')
    # Remove images
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    # Remove HTML tags
    text = re.sub(r'</?[^>]*>', '', text)
    # Remove special characters
    text = re.sub(r'[#*`~\-–^=<>+|/:]', '', text)
    # Remove footnote references
    text = re.sub(r'\[[0-9]*\]', '', text)
    # Remove enumerations
    text = re.sub(r'[0-9#]*\.', '', text)

    return len(text.split())

def _slugify_header(text):
    text = text.lower().strip()
    # remove inline markdown formatting
    text = re.sub(r'[`*_~]', '', text)
    # [link text](url) -> link text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # remove most punctuation
    text = re.sub(r'[^\w\s-]', '', text)
    # whitespace -> hyphen
    text = re.sub(r'\s+', '-', text)
    # collapse repeated hyphens
    text = re.sub(r'-+', '-', text)

    return text.strip('-')

# check all required keys exist

required_keys = ['slug', 'title', 'description', 'start_date', 'category', 'type', 'images']

optional_keys = ['url']

categories = ['all','featured','development','media','posts','homelab']

def check_for_length(post, key, char, string, min_length, max_length):
    content_length = len(string) if char == 'char' else _count_words_in_markdown(string)
    if not (min_length <= content_length <= max_length):
        logger.warning(f"Post {post.get('slug', 'unknown')}: '{key}' length is {content_length}, but should be between {min_length} and {max_length}.")
        return False
    return True

def check_image(image_url):
    if image_url.startswith("/static/"): # from this site
        if not image_url.startswith("/static/images/"):
            logger.warning(f"Image {image_url}: Should be in /static/images/.")
        image_path = Path("static") / image_url[len("/static/"):]
        if not image_path.exists() or not image_path.is_file() or image_path.stat().st_size == 0:
            logger.error(f"Image {image_url} is invalid.")
            return False
        elif not image_url.endswith(('.webp', '.gif')):
            logger.warning(f"Image {image_url} not converted to webp.")
            return False
        elif image_path.stat().st_size > 500 * 1024:
            logger.warning(f"Image {image_url} is larger than 500KB.")
            return False
    elif "vttc08.github.io" in image_url: # my own site
        logger.error(f"Image {image_url}: Potentially hardcoded URL.")
        return False
    elif not image_url.endswith(('.webp','.gif',".jpg",".jpeg",".png",".svg",".avif")): # other hosted images
        logger.error(f"Image {image_url} is not in a supported format.")
        return False
    elif image_url.startswith("https://"): pass
    else: # catches all cases (http://, empty url, invalid scheme)
        logger.error(f"Image {image_url} is invalid.")
        return False
    return True

def check_url(url, headers):
    file = url.split("#")[0]
    if urlparse(url).scheme:
        return True  # External URL, assume valid
    if file != "" and not (Path('content') / f"{file}.md").exists():
        logger.error(f"URL {url} does not point to a valid file.")
        return False
    if file == "" and len(url.split("#")) > 1:
        anchor = url.split("#")[1]
        if anchor not in headers:
            logger.error(f"URL {url} does not point to a valid anchor.")
            return False
    return True

def check_date(key, date_input):
    if isinstance(date_input, date):
        return True
    if key == 'start_date' and isinstance(date_input, str) and date_input.strip():
        return True
    logger.error(f"Post {key}: Date {date_input} is not a valid date object.")
    return False

def process_one(data):
    slug = data.get('slug', 'unknown')
    logger.info(f"======== Processing card: {slug} ========")
    for key in required_keys:
        if key not in data:
            logger.error(f"Post {slug}: Missing required '{key}'")
            return False
    for key in optional_keys:
        if key not in data:
            logger.warning(f"Post {slug} do not have '{key}'")
    # Check category
    if data['category'].lower() not in categories:
        logger.warning(f"Post {slug}: Invalid category '{data['category']}'.")
    # Check title length
    check_for_length(data, 'title', 'word', data['title'], 1, 15)
    # Check description length
    check_for_length(data, 'description', 'word', data['description'], 60, 80)
    # Check type length
    check_for_length(data, 'type', 'char', data['type'], 5, 40)
    # Featured is boolean
    if not isinstance(data.get('featured', False), bool):
        logger.error(f"Post {slug}: 'featured' should be a true/false value.")
        return False
    # Images check
    if not data['images'] or len(data['images']) < 1:
        logger.error(f"Post {slug}: 'images' must contain at least one image.")
        return False
    for image in data['images']:
        if not image.get('alt'):
            logger.warning(f"Image {image.get('url', 'unknown')} is missing 'alt' text.")
        if not check_image(image.get('url', '')):
            return False
    # start date and end date
    for date_key in ['start_date', 'end_date']:
        if date_key in data and not check_date(date_key, data[date_key]):
                return False
    return True

def process_markdown_frontmatter(post_file):
    with open(post_file, 'r', encoding='utf-8') as f:
        content = f.read()
        frontmatter_seen = 0
        ln_no = 0
        for line_number, line in enumerate(content.splitlines(), start=1):
            if frontmatter_seen == 2 and line.strip() != "":
                ln_no = line_number
                break
            if line.strip() == '---':
                frontmatter_seen += 1
    try:
        post = frontmatter.load(post_file)
    except (FileNotFoundError, yaml.YAMLError) as e:
        logger.error(f"Error loading {post_file}: {e}")
        return False

    for key in ("title","date"):
        if key not in post.metadata:
            logger.error(f"Post {post_file}: Missing required '{key}' in frontmatter.")
            return False

    if not isinstance(post.metadata.get('title',""), str) or not post.metadata['title'].strip():
        logger.error(f"Post {post_file}: 'title' must be a non-empty string.")
        return False

    if not isinstance(post.metadata.get('date',""), date):
        logger.error(f"Post {post_file}: 'date' must be a valid date.")
        return False

    check_markdown_content(post.content, line_start=ln_no)
    return True

def check_markdown_content(markdown_content, line_start=1):
    markdown_lines = markdown_content.splitlines()
    # Count fence lines, not backticks that may appear inside code or inline text.
    fence = None
    for line_number, line in enumerate(markdown_lines, start=line_start):
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if not fence and match:
            fence = match.group(1)
            unclosed_fence_line = line_number
        elif fence and match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
            fence = None
    if fence:
        logger.error(f"Line: {unclosed_fence_line} - Unclosed code block detected.")
    admonition_pattern = r'^\s*(?:!!!|\?\?\?\+?)\s+([A-Za-z0-9_-]+)(?:\s+"([^"]*)")?\s*$'
    got_admonition = False
    headers = re.findall(r'^(#{1,6})\s+(.+)$', markdown_content, flags=re.MULTILINE)
    # Check for no headers
    if len(headers) == 0 or not any(len(h[0]) > 1 for h in headers):
        logger.warning("Line: N/A - No ## or deeper headers found in markdown content.")
    for line_number, line in enumerate(markdown_lines, start=line_start):
        # Check for non note admonition and back to back admonitions
        if got_admonition and re.search(admonition_pattern, line):
            logger.error(f"Line: {line_number} - Back-to-back admonitions detected at line {line_number}: {line}")
        if line.strip():
            if got_admonition and line.startswith(" "):
                spaces = len(line) - len(line.lstrip())
                if spaces < 4:
                    logger.warning(f"Line: {line_number} - Admonition content is not indented properly: {line[:30]}...")
            elif not line.startswith(" "):
                got_admonition = False

        match = re.search(admonition_pattern, line)
        if line.startswith(("!!!", "???")) and not match:
            logger.error(f"Line: {line_number} - Invalid admonition format: {line}")
        if match:
            admonition_type = match.group(1)
            if admonition_type.lower() != "note":
                logger.error(f"Line: {line_number} - Only 'Note' admonitions are allowed. Got '{admonition_type}'.")
            got_admonition = True
    # Check for images ![alt text](image_url) and links [link text](link_url)
    image_regex = r'!\[([^\]]*)\]\(([^)]+)\)'
    images = re.findall(image_regex, markdown_content)

    image_links = [i[1]for i in images]

    for image_url in image_links:
        check_image(image_url)

    link_regex = r'(?<!\!)\[([^\]]+)\]\(([^)]+)\)'
    links = re.findall(link_regex, markdown_content)

    for text, link in links:
        if text.strip() == "" or link.strip() == "":
            logger.warning(f"Line: {line_number} - Link with empty text or URL found: {link}")
        check_url(link, [_slugify_header(h[1]) for h in headers])


    return True

class ErrorCounter(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.count = 0

    def emit(self, record):
        self.count += 1


def check_pymarkdown(post_file):
    pymarkdown = Path(sys.prefix) / "bin" / "pymarkdown"
    command = [
        str(pymarkdown),
        "--enable-extensions",
        "front-matter,markdown-tables",
        "-d",
        "*",
        "-e",
        "MD025,MD032,MD045",
        "scan",
        str(post_file),
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except OSError as error:
        logger.warning(f"PyMarkdown could not scan {post_file}: {error}")
        return

    output = result.stdout.strip()
    if output:
        for line in output.splitlines():
            # /home/kevin/Documents/portfolio/content/post.md:286:1: MD045: Images should have alternate text (alt text) (no-alt-text)
            match = m = re.match(r"^.*?:(\d+):\d+:\s+(.*)$", line)
            if match:
                line_number = match.group(1)
                message = match.group(2)
                logger.warning(f"Line: {line_number} - {message}")
            else:
                logger.warning(line)
    elif result.returncode:
        logger.warning(
            "PyMarkdown could not scan %s (exit code %s).",
            post_file,
            result.returncode,
        )

def main():
    errors = ErrorCounter()
    logger.addHandler(errors)
    try:
        try:
            with open('site.yaml', 'r') as f:
                site_data = yaml.safe_load(f)
        except (yaml.YAMLError, FileNotFoundError) as e:
            logger.error(f"Error loading site.yaml: {e}")
            return 1

        if not isinstance(site_data, list):
            logger.error("site.yaml must contain a list of posts.")
            return 1

        posts = []
        for index, data in enumerate(site_data, start=1):
            if not isinstance(data, dict):
                logger.error(f"Post {index} must be a mapping.")
            else:
                posts.append(data)

        duplicates = [slug for slug, count in Counter(data.get('slug', 'unknown') for data in posts).items() if count > 1]
        for duplicate in duplicates:
            logger.error(f"Duplicate entry: {duplicate}")

        for data in posts:
            process_one(data)
        # Markdown frontmatter check
        for post_file in Path("content").glob("*.md"):
            logger.info(f"======== Processing post: {post_file} ========")
            process_markdown_frontmatter(post_file)
            check_pymarkdown(post_file)

        return 1 if errors.count else 0
    finally:
        logger.removeHandler(errors)

    # check markdown frontmatter


if __name__ == '__main__':
    sys.exit(main())
