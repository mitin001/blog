cd ..
grep -r '^## ' 2025/09/[23]* | awk '{print NR":## "$0}' > faq/txt/2025-09-2.txt

cat faq/prompt.txt > faq/prompts/2025-09-2.txt
cat faq/txt/2025-09-2.txt | awk -F':## ' '{print $1, $3}' >> faq/prompts/2025-09-2.txt
cat faq/prompts/2025-09-2.txt | pbcopy
# send faq/prompts/2025-09-2.txt to chatgpt and get back faq/classifications/2025-09-2.json
subl faq/classifications/2025-09-2.json

cat faq/txt/2025-09-2.txt | awk -F':## ' '{print $1"\t"$2"\t"$3}' | jq -Rn '[inputs | split("\t") | { (.[0]): .[1:] }] | add' > faq/json/2025-09-2.json

cd faq
python3 faq.py json/2025-09-2.json classifications/2025-09-2.json disciplines.json ../faq.md
