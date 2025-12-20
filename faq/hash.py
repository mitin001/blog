import re


def github_heading_id(heading: str) -> str:
    """
    Generate a GitHub-style heading id from a Markdown heading text.
    Does not handle duplicate-avoidance; identical headings -> identical ids.
    https://www.perplexity.ai/search/i-made-a-heading-in-readme-md-xkAtbM.XSA.3TUHQF6q_LQ#1
    """
    slug = heading.lower()

    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')

    # Remove punctuation / symbols that GitHub strips from IDs
    slug = re.sub(r'[`~!@#$%^&*()+=<>?,./:;\"\'|{}\[\]\\–—]', '', slug)

    # Optionally also strip common CJK punctuation (GitHub does this too)
    slug = re.sub(r'[　。？！，、；：“”【】（）〔〕［］﹃﹄“”‘’﹁﹂—…－～《》〈〉「」]', '', slug)

    # Collapse multiple hyphens to one
    slug = re.sub(r'-{2,}', '-', slug)

    # Trim leading/trailing hyphens
    slug = slug.strip('-')

    return slug
