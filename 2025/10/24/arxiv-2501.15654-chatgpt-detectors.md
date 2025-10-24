# [People who frequently use ChatGPT for writing tasks are accurate and robust detectors of AI-generated text](https://arxiv.org/abs/2501.15654)

This academic paper was referenced by [Wikipedia's essay on spotting signs of AI writing](../../../2025/10/11/wikipedia-signs-of-ai-writing.md). It answered two questions about LLMs.

## What do the experts in AI writing focus on when determining whether the text they're classifying was written by AI or a human?

> Usage of “AI vocabulary” (e.g., vibrant, crucial, significantly) form the most common giveaways. Close behind are formulaic sentence and document structures (e.g., optimistically vague conclusions) and originality (how creative or engaging an article is).

The AI vocabulary differs from the human vocabulary, not necessarily in the words that occur in them, but in their distribution.

> LLMs use specific words and phrases more often than human writers, which often results in repetitive, unnatural, or overly complex wording.

AI clichés stick out of the text like sore thumbs.

> The “testament” serving “as a beacon of hope and inspiration” and “demonstrating” to us humans “that anything is possible.”

AI cannot replicate the randomness of the way humans spill their thoughts on paper.

> AI-generated sentences follow predictable patterns (e.g., high frequency of “not only ... but also ...”, or con-sistently listing three items), while human-written sentences vary more in terms of length.

Human writing will often surprise you.

> It’s offset by some great analogies and creative phrasing that works well to convey the topic, such as with "amateur sleuths", "catnip for a certain type of Reddit user."

AI writing will make you roll your eyes and cringe.

> What happens when AI tries to be creative? Penguins "stand on their own flippers".

When humans try to embed spoken quotes into their writing, they usually don't fit in perfectly. This is because speech and writing differ in tone, and humans can tell when the tone shifts.

> The quotes being short snippets also makes me think they’re real, as the writer had to find a way to fit them into the text, rather than them just perfectly stating either side’s views.

Such a tonal shift is too subtle for AI to fake.

> The quotes also feel fake, every expert speaks the same way and it’s too homogenous with the text.

AI will make up the supposed quotes with the same tone as the text supposedly written by someone merely embedding the "quotes" into their article.

> AI-generated quotes sound overly formal, lack the varied nuances of real conversation, and often mirror the article’s main text too closely in style.

The quotes made up by AI are blatantly fake.

> Experts flagged quotes that were always in the same format and style (e.g., only placed at the end of each paragraph).

Humans aren't interested in the words that should appear in the text if we follow statistical patterns of similar texts. Humans are interested in text that makes a point and is to the point.

> AI-generated text often lacks concise flow by overexplaining or including irrelevant details.

Humans want to be surprised. They want brand-new sentences. They don't want clichés.

> AI-generated text is much less creative than that of humans, lacking originality and sticking to an ‘obvious’ way to answer a prompt. Humans incorporate twists, unexpected insights.

Human beings express emotions in their writing even when they're trying not to. Human writing comes alive to the reader. AI writing is soulless and dead.

> The tone of AI-generated text is consistently neutral or positive, lacking depth or emotional variety.

AI-generated writing is emotionless aside from its irritating bumbling positivity.

> The writing is filled with the same language it uses to describe everything - inspirational, stunning, essential, and resonating - using formal words, an inherent positivity bias, and a reflective, romantic tone that doesn’t give details on why this topic matters.

Humans know how to get the attention of their fellow humans.

> Human introductions have more compelling hooks.

We know how to suck the reader into our world: by telling them a story.

> The introduction is unique as it starts with the subject of the article watching a movie rather than instantly explaining the entire point of the article.

AI is also often wrong but never in doubt.

> Incorrect information delivered with customary AI confidence.

What sets experts in AI detection from nonexperts is their knowledge of the details that give away the origin of a given text. It's not just any fancy word that points to the AI origin of a corpus of text; there is a characteristic AI vocabulary. It's also a common misconception that AI can write neutrally but with syntax errors. The opposite is true.

> Nonexperts take the inclusion of any “fancy” or otherwise low-frequency word types as signs of AI-generated text; in contrast, experts are much more familiar with exact words and phrases overused by AI (e.g., testament, crucial). Non-experts also believe that human authors are more likely than AI to form grammatically-correct sentences, while experts realize the opposite is true: humans actually make more grammatical errors. Finally, nonexperts attribute any text written in a neutral tone to AI, resulting in many false positives.

These techniques work so well for experts that they retain their AI detection accuracy even for generated text that's gone through extensive paraphrasing.

> Paraphrasing is not an effective attack on expert human detectors.

## If you prompt an LLM to avoid sounding like an LLM with detailed instructions about what gives away the AI-generated nature of a given text elicited from human experts in classifying AI writing, will its outputs then evade detection by said experts?

No, this study tried to prompt the paid version of the most advanced LLM available (O1-PRO), and it still couldn't produce an output that would be misclassified as human-written by human experts.

> Despite our best efforts to generate articles that our experts would find undetectable, most of their detection rates remain largely unchanged from prior experiments, and the expert majority vote is again perfect on all 60 articles.

AI cannot humanize its output. Even if you ask it to avoid putting AI tells into them, with those tells explicitly spelled out in the prompts, the LLM will still include them.

> Humanization does not completely remove the “AI signature” from texts.

Paraphrased articles sound even more AI-generated to experts than articles generated in a single prompt.

> Annotators continue to pick up on many of the same clues within the paraphrased articles that were also apparent in Experiments 1 & 2, such as high frequency of “AI vocab” (even after paraphrasing), formulaic sentence structures, and cheerful summary conclusions. Somewhat counterintuitively, explanations about paraphrased articles note AI vocab in 88% of explanations, compared to only 69.8% of non-paraphrased GPT-4o articles.

The more revisions an LLM makes to its own text, the more AI signatures it embeds in them, even when explicitly told not to do so.
