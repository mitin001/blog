find 2025 -name "*.md" | grep -v "/pivot-" | grep -v "/maddow-" | grep -v "/darknetdiaries-" | parallel python3 readme.py {} readme.md
cd series
find .. -name "*.md" | grep "/pivot-" | parallel python3 readme.py {} pivot.md
find .. -name "*.md" | grep "/maddow-" | parallel python3 readme.py {} maddow.md
find .. -name "*.md" | grep "/darknetdiaries-" | parallel python3 readme.py {} darknetdiaries.md
