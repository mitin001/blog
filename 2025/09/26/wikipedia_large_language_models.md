# [Large language models](https://en.m.wikipedia.org/wiki/Wikipedia:Large_language_models)

After reading through an [explosive discussion] among the Wikipedians protesting the use of AI, I dug deeper into the project and found an essay on the matter. It answered three more questions I had about LLMs.

[explosive discussion]: ../../../2025/09/25/wikipedians-discuss-simple-summaries.md

## If an LLM is an averaging machine, how can it output ideas never before seen anywhere?

An LLM returns the average of all text it's been trained on, with filters. (The filters ensure only the text relevant to the query is considered.) Averaged text can consist of brand-new sentences. The phrases "original research" and "algorithmic bias" may exist in the same article (e.g., an essay by a Wikipedian), but an LLM can be prompted in such a way that it would create a brand-new phrase like "original bias" or "algorithmic research" in the context where these phrases have never been used before. Not every combination of words has been published before. Because AI is in the business of combining words together, it can occasionally stumble into a brand-new sentence. However, even though the words in such a "sentence" seem to occur together a lot does not mean they actually state a fact.

> LLMs are pattern completion programs: They generate text by outputting the words most likely to come after the previous ones. They learn these patterns from their training data, which includes a wide variety of content from the Internet and elsewhere, including works of fiction, low-effort forum posts, unstructured and low-quality content for search engine optimization (SEO), and so on. Because of this, LLMs will sometimes "draw conclusions" which, even if they seem superficially familiar, are not present in any single reliable source.

If an LLM can garble high-quality text into nonsense by virtue of averaging, imagine what happens when it's averaging low-quality text. 

## How do LLMs exploit human weaknesses to seem more than they are? 

LLMs are nothing more than autocomplete. They filter and average their training data. However, when human encounter LLM outputs, they anthropomorphize them. They ascribe to them the characteristics of human authors, entities that are actually capable of creating text with meaning. Such inappropriately ascribed characteristics include confidence, reasoning, and analysis. LLMs are not capable of exhibiting any of those characteristics, which is problematic for those people who interpret them as signals of trustworthiness.

> Since their outputs are typically plausible-sounding and given with an air of confidence, any time that they deliver a useful-seeming result, people may have difficulty detecting the above problems. An average user who believes that they are in possession of a useful tool, who maybe did a spot check for accuracy and "didn't see any problems", is biased to accept the output as provided; but it is highly likely that there are problems.

To not get bogged down in minutiae, we rely on heuristics. If a source has given you information you once deemed accurate, you will believe everything it gives you from that point on. If a source sounds confident or well-reasoned, we take it as evidence of expertise. Such heuristics, coupled with the novelty of an emerging technology such as an LLM, is a recipe for misplaced optimism in this technology. Cue a lawyer who cites cases imagined by an LLM in the court of law as precedent because he trusts an LLM more than he does the law library.

## What does an LLM do when asked about an obscure subject for which there's not enough text in its training data?

Wikipedians asked Gemini about a fictitious species of pademelon, and its confidently asserted that such a species existed and provided sentences that could fit the description of a different species.

> In order to provide the most plausible answer, it extracted general information about a different kind of pademelon.

AI will never contradict the prompt, and it will fit the words from its training data to it, just based on similarity of the words, even when they make for false statements.

> LLM's can offer statements with a confident tone even when that information is factually incorrect or unverifiable.

# Next

* [Chatbot comments in discussions](../../../2025/10/07/wikipedia_chatbot_comments_in_discussions.md)
