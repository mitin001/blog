for f in 2025/*/*/*; do
  [ -f "$f" ] && ! gsed '1b; /^#/q; p' "$f" | grep -q '../../..' && echo "$f"
done
