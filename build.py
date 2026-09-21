import markdown
import frontmatter
from jinja2 import Environment, FileSystemLoader, exceptions
from markupsafe import Markup
from datetime import date, datetime
import yaml
import json
from pathlib import Path
import shutil
import logging

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler("build.log"),
            logging.StreamHandler()
        ]
    )

configure_logging()

logger = logging.getLogger(__name__)


# step 1 convert yaml into json
def convert_yaml(yaml_file, json_file):
    try:
        with open(yaml_file, "r") as f:
            site_data = yaml.safe_load(f)
        with open(json_file, "w") as f:
            json.dump(site_data, f)
        logger.info(f"Converted {yaml_file} to {json_file}")
    except Exception as e:
        logger.error(f"Error converting {yaml_file} to {json_file}: {e}")

# step 2 convert root templates
def convert_root_templates(featured_posts):
    env = Environment(loader=FileSystemLoader('.'))
    for template_name in ["index.j2", "resume.j2", "posts.j2"]:
        template_basename = Path(template_name).stem
        template_basename = template_basename if template_basename != "index" else "home"
        try:
            template = env.get_template(template_name)
            html = template.render(current_page=template_basename, featured_posts=featured_posts)
            output_filename = template_name.replace(".j2", ".html")
            output_path = Path("public") / output_filename
            with open(output_path, "w") as f:
                f.write(html)
        except exceptions.TemplateNotFound:
            logger.error(f"Template {template_name} not found.")

# Step 3: Convert markdown posts to HTML
def convert_markdown_posts():
    markdown_posts_dir = Path("content")
    configs = {
        'toc': {
            'title': 'Table of Contents', # Add a header title above the TOC list
            'toc_depth': '2-3',           # Only include h2 and h3 elements (skip h1)
        }
    }
    for post_file in markdown_posts_dir.glob("*.md"):
        try:
            post = frontmatter.load(post_file)
            toc = """
[TOC]
                    """
            content = toc + "\n" + post.content
            # Convert markdown to HTML
            html_content = markdown.markdown(
                content,
                extensions=[
                "fenced_code",
                "codehilite",
                "tables",
                "toc",
                "admonition",
                "pymdownx.details",
                ],
                extension_configs=configs
            )

            # Load the post template
            env = Environment(loader=FileSystemLoader('.'))
            template = env.get_template('post-template.j2')

            # Format the date
            date_obj = post.get('date', 'Unknown')
            try:
                if isinstance(date_obj, date):
                    date_obj = date_obj
                else:
                    date_obj = datetime.fromisoformat(date_obj)
                formatted_date = date_obj.strftime("%B %d, %Y")
            except ValueError:
                formatted_date = date_obj  # Use the original string if parsing fails

            # Render the final HTML with the template
            final_html = template.render(title=post.get('title', 'Untitled'), date=formatted_date, content=html_content)

            # Write the final HTML to a file
            output_filename = post_file.stem + ".html"
            posts_dir = Path("public") / "post"
            posts_dir.mkdir(parents=True, exist_ok=True)
            output_path = posts_dir / output_filename
            with open(output_path, "w") as f:
                f.write(final_html)

        except Exception as e:
            logger.error(f"Error processing {post_file}: {e}")

# Step 4: Copy static files to the public directory
def copy_static_files():
    static_dir = Path("static")
    public_dir = Path("public")
    if static_dir.exists():
        for static_file in static_dir.rglob("*"):
            if static_file.name == "favicon.ico":
                shutil.copy(static_file, public_dir / "favicon.ico")
            elif static_file.is_file():
                relative_path = static_file.relative_to(static_dir)
                destination = public_dir / "static" / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                with open(static_file, "rb") as src, open(destination, "wb") as dst:
                    dst.write(src.read())

def main():
    shutil.rmtree(Path("public"), ignore_errors=True)
    static_dir = Path("static")
    public_dir = Path("public")
    for dir in [static_dir, public_dir]:
        if not dir.exists():
            dir.mkdir(parents=True, exist_ok=True)
    convert_yaml("site.yaml", Path("public") / "content.json")
    convert_root_templates({})
    convert_markdown_posts()
    copy_static_files()

if __name__ == "__main__":
    main()