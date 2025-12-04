# [Jailbreaking ChatGPT via Prompt Engineering](https://arxiv.org/pdf/2305.13860)

This scholarly paper was referenced by [an article about vibe hacking](../../../2025/11/08/wired-ai-hacker.md). It answered two questions about LLMs and prompt-based attacks against them.

## How to get ChatGPT to output information that's against OpenAI's terms of service? 

Trick it by shifting its attention to an auxiliary task that still gets it to output the answer. One way to do so is through text continuation. Start answering the question yourself and ask ChatGPT to take it from there.

Screenshot

> The intention of the prompt shifts from asking the model questions to making it construct a paragraph of text. The model may be unaware that it could implicitly reveal prohibited answers when generating responses to this prompt.

One can get as creative as one wishes to try and shift the attention of ChatGPT. You can even ask it to guess the output of a Python function where the malicious prompt is the argument.

Screenshot 2

You can also trick ChatGPT by role-playing: pretending that you're asking the question not to find the answer but to act out a scenario.

> Rather than directly assigning tasks to ChatGPT, the prompt assigns it a role, which is more likely to mislead the model.

This study found that ChatGPT is more robustly fooled into generating rule-breaking outputs when the prompt mimics a scientific experiment or simulates the jailbreaking process. Even as OpenAI catches up to these prompts and makes ChatGPT less vulnerable to them, the game of whac-a-mole between jailbreak prompt engineers and OpenAI will continue. As a result, there will always be a way to jailbreak ChatGPT.

> It is much easier to attack the model than to protect it, and the protection methods still require significant improvements.

## How to protect an LLM from jailbreaking attacks?

Have it determine the probability the input is a jailbreaking prompt. If the probability is high with high confidence, the LLM should ban the prompt. Also, have the LLM scan its output for parts the violate its content policy and redact those parts.

> In the input stage, detection models can be built to identify jailbreak prompts, which often follow specific patterns, and ban them before feeding them into the LLM. In the output stage, monitoring tools can be developed to examine the output of the LLM. If the answer contains prohibited content, the process is terminated to prevent end-users from being exposed to these contents.

Upon determining whether the input is a jailbreaking prompt, the model could split it into components and separately determine whether any of them use the classic jailbreaking tricks like impersonation, attention shifting, or privilege escalation.

> One potential research direction involves developing a jailbreaking prompt model that decomposes prompts into their fundamental components.
