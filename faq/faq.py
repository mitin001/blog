#!/usr/bin/env python3
import sys
import json
from hash import github_heading_id

if len(sys.argv) != 5:
    print("Usage: python script.py questions.json topics.json disciplines.json faq.md")
    sys.exit(1)

questions_file, topics_file, disciplines_file, output_file = sys.argv[1:5]

with open(disciplines_file, "r", encoding="utf-8") as f:
    disciplines = json.load(f)
with open(topics_file, "r", encoding="utf-8") as f:
    topics = json.load(f)
with open(questions_file, "r", encoding="utf-8") as f:
    questions = json.load(f)

# Open for append mode ('a') so it doesn't overwrite existing content
with open(output_file, "a", encoding="utf-8") as out:
    for top_level, subdisciplines in disciplines.items():
        out.write(f"\n## {top_level}\n")
        for sub in subdisciplines:
            if sub not in topics.keys():
                raise Exception("Subdiscipline not in topics")
            if topics[sub]:
                out.write(f"\n### {sub}\n\n")
                for q_num in topics[sub]:
                    (md_file, question) = questions[str(q_num)]
                    out.write(f"* [{question.strip()}]({md_file}#{github_heading_id(question)})\n")
