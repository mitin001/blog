# [Knowledge Does Not Protect Against Illusory Truth](https://dx.doi.org/10.1037/xge0000098)

This scholarly paper was referenced by [Wikipedia's article about the illusory truth effect](../../../2025/10/25/wikipedia_illusory_truth_effect.md). It answered three questions about vulnerabilities in human cognition as they relate to judging the truth of a given statement.

## When we confidently determine whether a statement is true or false, do we always recall how we learned it? 

No, like LLMs, we cannot always cite our sources.

> Much of the information in the knowledge base comes to mind relatively automatically, without the experience of reliving the original learning event.

When I tell someone that almost 70% of taxes is paid by the richest 10% of the population, I remember Scott Galloway saying this on a podcast, followed by my disbelief and confirming said fact by locating reliable sources on the web. But when I say that some wealthy people avoid paying taxes by putting their wealth into shell companies in tax havens, I can't recall where I learned that. I vaguely remember reading it in some trusted periodical like the New York Times, but it could've just been some propaganda material I stumbled upon in some sketchy corner of the web. If I wanted to make this statement in writing, I would need to find a new reliable source to confirm this statement, not necessarily the one where I actually learned it (because I don't remember it), like what an LLM does when it tries to cite sources for sentences it constructs out of words that fit together statistically based on the distributions in the training corpora. This makes an LLM susceptible to bias injection (e.g., if the training corpora often place the words "tax evasion" near the words "wealthy" or "top 1%"), and the related inability to cite sources in humans makes us susceptible to repeating falsehoods planted by propagandists.

> People rarely engage in source monitoring when evaluating information stored in their knowledge bases. This nonevaluative tendency may render people especially susceptible to external influences like fluency.

We could misjudge ourselves to be so fluent in a given subject that we simply accept whatever statement made about it to be true. Our high fluency in it convinced us that no further critical evaluation of the statement was necessary.

## If we already know if a statement is false, why do we sometimes erroneously label it as true?

Because we don't always get to make decisions based on knowledge-retrieval. To err is human, and human error arises from human complexity. We have competing systems in our brains that give different answers to the same questions, and we don't always consult the same system. Sometimes, we assess whether a statement is true not based on our prior knowledge of whether it was true, but automatically. The researchers call this competing knowledge assessment system that doesn't rely on knowledge-retrieval _fluency_.

> It is possible for participants to rely on fluency despite having contradictory knowledge stored in memory.

This is known as _knowledge neglect_. When we rely on fluency, we short-circuit knowledge-retrieval. This is why we can misjudge the truth of something we know to be true or false. Repetition feeds fluency, so if repeatedly encounter a false statement, it won't necessarily override our knowledge, but it affects our fluency.

> Repetition increased statements’ perceived truth, regardless of whether stored knowledge could have been used to detect a contradiction. Reading a statement like “A sari is the name of the short pleated skirt worn by Scots” increased participants’ later belief that it was true, even if they could correctly answer the question “What is the name of the short pleated skirt worn by Scots?”

This is why repeatedly seeing myths or misleading statements affects the behaviors of the people who know them to be false or misleading. And yet, when someone who knows better is repeatedly exposed to the myth that vitamin C guards against colds will still find himself buying vitamin C supplements from the store, a decision made in the spur of the moment without consulting the knowledge-retrieval circuit of the brain. This is how falsehoods injected by propagandists move society in the direction they choose.

## How to effectively misinform people?

Give them the illusion of knowledge. This is what the authors one of the cited studies did with their subjects.

> Participants read a series of words, some of which were semantically related to the answers for a later general knowledge test. Later, participants not only incorrectly answered questions with the lures they saw earlier, but did so with high confidence.

Make the participants believe they have high fluency on a given subject and they will later bypass the critical evaluation of a relevant statement and simply regard it as true. We conserve our mental resources whenever we can.

> People automatically assume that a statement is true because “unbelieving” comprises a second, resource-demanding step. Even when people devote resources to evaluating a claim, they only require a “partial match” between the contents of the statement and what is stored in memory.

In giving someone the illusion of knowledge, it is not even necessary to make your falsehoods standalone statements.

> The Atlantic Ocean is the largest ocean on Earth.

You can embed them in fictional stories for higher engagement.

> Paddling across the largest ocean, the Atlantic.

Make your falsehoods semantically related.

> We tend to notice errors that are less semantically related to the truth.

LLMs are particularly good at planting such falsehoods (hallucinating) because they put semantically-related words together by design, even when doing so results in a false statement.

> How many animals of each kind did Moses take on the ark?

If Moses dominates the training corpora of an LLM relative to Noah (the one with the ark), then an LLM will incorrectly make ark-related statements about Moses. Humans will often also miss this error because of the semantic relatedness of these words. If, however, an LLM makes such a statement about Adam, humans are less likely to miss this error because Adam and Noah are much less semantically related than Moses and Noah.

> How many animals of each kind did Adam take on the ark?

The ease with which we spot errors made by LLMs depends on the semantic relatedness of the words in the output.

> We expect that participants would draw on their knowledge, regardless of fluency, if statements contained implausible errors (e.g., “A grapefruit is a dried plum,” instead of “A date is a dried plum”); in this example, the limited semantic overlap of the words grapefruit and plum would yield an insufficient match.

Because LLMs select words that are as semantically related as possible, the hallucinations in their outputs will often be hard for humans to find. They will not typically confuse grapefruits for prunes (an error a human can easily spot) but will easily confuse dates for prunes (an error that is much harder for a human to spot).
