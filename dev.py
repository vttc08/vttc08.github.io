import os
import threading
from fnmatch import fnmatch
from pathlib import Path

from livereload import Server
from tornado.web import StaticFileHandler
from watchfiles import watch

from build import convert_markdown_posts, convert_root_templates, copy_static_files

PUBLIC_DIR = Path("public").resolve()


class ExtensionlessStaticFileHandler(StaticFileHandler):
    """Serve ``/page`` from ``public/page.html`` during development."""

    def validate_absolute_path(self, root, absolute_path):
        if (
            not os.path.exists(absolute_path)
            and not self.request.path.endswith("/")
            and not Path(absolute_path).suffix
        ):
            html_path = f"{absolute_path}.html"
            if os.path.isfile(html_path):
                absolute_path = html_path

        return super().validate_absolute_path(root, absolute_path)

def assets_filter(change, path):
    # The watcher starts at the repository root, so generated files in public/
    # would otherwise be treated as source changes and trigger another build.
    if Path(path).resolve().is_relative_to(PUBLIC_DIR):
        return False

    return \
        fnmatch(path, "*.md") or \
        fnmatch(path, "*.j2") or \
        fnmatch(path, "*.yaml") or \
        fnmatch(path, "*.css") or \
        fnmatch(path, "*.js")

def watch_files():
    for changes in watch('.', watch_filter=assets_filter):
        for change, path in changes:
            print(f"Detected change in {path}. Rebuilding...")
            # convert_yaml("site.yaml", "public/content.json")
            convert_root_templates()
            convert_markdown_posts()
            copy_static_files()

def main():
    server = Server()
    server.SFH = ExtensionlessStaticFileHandler
    server.watch('public/*.html')
    server.watch('public/*.js')
    server.watch('public/*.css') # Watch specific folders if needed

    server_thread = threading.Thread(
        target=server.serve,
        kwargs={'root': './public', 'host': "0.0.0.0", 'port': 5501},
        daemon=True,
    )
    watcher_thread = threading.Thread(target=watch_files, daemon=True)

    server_thread.start()
    watcher_thread.start()
    server_thread.join()
    watcher_thread.join()


if __name__ == "__main__":
    main()
