# pair every backlink with a forward link in the Next section of the backlinked doc
ggrep -rH -oP '(?<=\.\./\.\./\.\./)2025[^ ]*md' 2025 | awk -f filter_singly_linked.awk | sort | python3.13 next.py

sh find_roots.sh | python3.13 readme.py
