find 2025 -name "*.md" | grep -v "/pivot-" | grep -v "/maddow-" | grep -v "/darknetdiaries-" | parallel python3 readme.py {} readme.md
find 2025 -name "*.md" | grep "/pivot-" | parallel python3 readme.py {} series/pivot.md
find 2025 -name "*.md" | grep "/maddow-" | parallel python3 readme.py {} series/maddow.md
find 2025 -name "*.md" | grep "/darknetdiaries-" | parallel python3 readme.py {} series/darknetdiaries.md
