find 2025 -name "*.md" | parallel python3 readme.py {}
find series -name "*.md" | parallel python3 readme.py {}
