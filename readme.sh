git pull

# pair every backlink with a forward link in the Next section of the backlinked doc
# ggrep -rH -oP '(?<=\.\./\.\./\.\./)2025[^ ]*md' 2025 | awk -f filter_singly_linked.awk | sort | python3.13 next.py
ggrep -rH -oP '(?<=\.\./\.\./\.\./)2025[^ ]*md' 2026 | awk -f filter_singly_linked.awk | sort | python3.13 next.py
# ggrep -rH -oP '(?<=\.\./\.\./\.\./)2026[^ ]*md' 2025 | awk -f filter_singly_linked.awk | sort | python3.13 next.py
# ggrep -rH -oP '(?<=\.\./\.\./\.\./)2026[^ ]*md' 2026 | awk -f filter_singly_linked.awk | sort | python3.13 next.py

git add . && git commit -m "Linking" && git push

sh find_roots.sh | python3.13 readme.py
git diff # see if there are new roots to explain in readme.md
