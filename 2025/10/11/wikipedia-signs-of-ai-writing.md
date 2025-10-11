# [Signs of AI writing](https://en.m.wikipedia.org/w/index.php?title=Wikipedia:Signs_of_AI_writing&oldid=1315853483)

This advice page was referenced by [WikiProject AI Cleanup](https://en.m.wikipedia.org/wiki/Wikipedia_talk:WikiProject_AI_Cleanup/Archive_1), which, in turn, was referenced by [Wikipedia's discussion about chatbot comments in discussions](../../../2025/10/07/wikipedia_chatbot_comments_in_discussions.md). It answered three questions about LLM detection.

## Why do LLMs prefer empty generalities over specific facts?

Due to regression toward the mean, a fundamental feature arising from the statistical nature of these models.

> LLMs (and artificial neural networks in general) use statistical algorithms to guess (infer) what should come next based on a large corpus of training material. It thus tends to regress to the mean; that is, the result tends toward the most statistically likely result that applies to the widest variety of cases. It can simultaneously be a strength and a "tell" for detecting AI-generated content. For example, LLMs are usually trained on data from the internet in which famous people are generally described with positive, important-sounding language. It will thus sand down specific, unusual, nuanced facts (which are statistically rare) and replace them with more generic, positive descriptions (which are statistically common). Thus the specific detail "invented a train-coupling device" might become "a revolutionary titan of industry." LLMs tend to smooth out unusual details and drift toward the most common, statistically probable way of describing a topic.

The paradox is that when the words become more nondescript as to apply to a wider array of related topics, they become less neutral. This is similar to when a realtor has nothing good to say about a house she's selling, she stops describing it as granite or something else specific and instead opts for "wonderful," "great neighborhood," and exclamation points.

> The subject becomes simultaneously less specific and more exaggerated.

## How to tell LLM-generated text from human-written text?

LLM-generated text exhibits a tendency to avoid the specifics to an infuriating degree.

> A smoothing over of specific facts into generic statements that could apply to many topics.

It keeps reminding the user that no portion of its endless wall of text strays from the prompt. Rather than giving the user something useful, it just repeats these reminders over and over again like a bad student who hasn't done his homework and is trying to bullshit through his book report.

> LLM writing often puffs up the importance of the subject matter with reminders that it represents or contributes to a broader topic. There seems to be only a small repertoire of ways that it writes these reminders.

It keeps repeating the same phrases.

> stands as / serves as / is a testament, plays a vital/significant/crucial role, underscores its importance, highlights its significance, continues to captivate, leaves a lasting impact, watershed moment, key turning point, deeply rooted, profound heritage, steadfast dedication, indelible mark, solidifies ...

The LLM's designers think an answer to every question needs to mention challenges, future prospects, and a conclusion. It's like the users won't call the LLM on its bullshit if it puffs up its responses with the same high-school-level formula for baffling teachers with teenage nonsense.

> Many LLM-generated Wikipedia articles include a "Challenges" section, which typically begins with a sentence like "Despite its [positive/promotional words], [article subject] faces challenges..." and ends with either a positive assessment of the article subject, or speculation about how ongoing or potential initiatives could benefit the subject.

## How to tell the output of a text-to-image model from the work of a photographer or graphic designer?

AI-generated images hide their tells in the details.

> They look acceptable at first glance, but specific details tend to be blurry and malformed. This is especially true for background objects and text.
