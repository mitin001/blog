BEGIN { FS=":" }

{
  a = $1
  b = $2
  if (a < b) key = a ":" b
  else       key = b ":" a
  line[NR] = $0
  k[NR] = key
  c[key]++
}

END {
  for (i = 1; i <= NR; i++)
    if (c[k[i]] == 1)
      print line[i]
}
