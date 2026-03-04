for f in 202[56]/*/*/*; do
  [ -f "$f" ] && ! gsed '1b; /^#/q; p' "$f" | grep -q '../../..' && echo "$f"
done
