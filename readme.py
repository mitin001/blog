from sys import argv
import markdown
from bs4 import BeautifulSoup

def md_to_txt(md_str):
    html = markdown.markdown(md_str)
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text().split('\n')[0]

md_filename = argv[1]
readme_filename = argv[2]

with open(readme_filename, 'a') as readme_file:
    # only add the link to the md file if the readme file doesn't already contain it
    if md_filename not in open(readme_filename, 'r').read():
        with open(md_filename, 'r', encoding='utf-8') as md_file:
            readme_file.write(f"* [{md_to_txt(md_file.read())}](/{md_filename})\n")
