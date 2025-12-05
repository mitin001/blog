import sys
import markdown
from bs4 import BeautifulSoup


def md_to_txt(md_str):
    html = markdown.markdown(md_str)
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text().split('\n')[0]


def get_link_text(filename):
    with open(filename, encoding="utf-8") as f:
        return md_to_txt(f.readline().strip())


def add_next_link(filename, link_text, link_href):
    with open(filename, 'r') as f:
        content = f.read()

        with open(filename, 'a') as f:
            if "# Next" not in content: # if the next section is missing, add it
                f.write("\n# Next\n\n")
            f.write("* [%s](%s)\n" % (link_text, link_href))


for line in sys.stdin:
    next_file, prev_file = line.strip().split(':', 1)
    link_text = get_link_text(next_file)
    add_next_link(prev_file, link_text, "../../../%s" % (next_file))
