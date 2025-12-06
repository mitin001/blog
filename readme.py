import sys
import markdown
from bs4 import BeautifulSoup


def md_to_txt(md_str):
    html = markdown.markdown(md_str)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text().split("\n")[0]


def get_link_text(filename):
    with open(filename, encoding="utf-8") as f:
        return md_to_txt(f.readline().strip())


with open("readme.md", "r") as f:
    with open("readme.md", "a") as readme_file:
        content = f.read()
        for line in sys.stdin:
            next_file = line.strip()
            link_text = get_link_text(next_file)
            if next_file not in content:
                # only add the link to the md file if the readme file doesn't already contain it
                readme_file.write("* [%s](%s)\n" % (link_text, next_file))
