find 2025 -name "*.md" \
| grep -v "/pivot-" | grep -v "/maddow-" | grep -v "/darknetdiaries-" | grep -v "/real-time-" | grep -v "/nnf-" \
| parallel python3 readme.py {} readme.md
cd series
find .. -name "*.md" | grep "/nnf-" | parallel python3 ../readme.py {} nnf.md
find .. -name "*.md" | grep "/pivot-" | parallel python3 ../readme.py {} pivot.md
find .. -name "*.md" | grep "/maddow-" | parallel python3 ../readme.py {} maddow.md
find .. -name "*.md" | grep "/real-time-" | parallel python3 ../readme.py {} real-time.md
find .. -name "*.md" | grep "/darknetdiaries-" | parallel python3 ../readme.py {} darknetdiaries.md
