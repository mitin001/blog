# [Cybercriminals experiment with AI on the dark web](https://dfi.kaspersky.com/blog/ai-in-darknet)

This post was referenced by [an article about vibe hacking](../../../2025/11/08/wired-ai-hacker.md). It answered two questions about the cybersecurity implications of ChatGPT.

## How could ChatGPT be making us less secure?

It potentially enables any script kiddie to get as far as a seasoned cybercriminal.

> It lowers the entry threshold for malicious actors.

ChatGPT can be used to slightly modify the code of given malware just enough to avoid detection by antivirus software.

> To generate polymorphic malware that can modify its code while keeping its basic functionality intact.

The malware can keep modifying itself while installed in the victim's device by simply making prompts to ChatGPT programmatically. Antivirus software won't suspect anything out of the ordinary here either since ChatGPT is a legitimate service.

> By accessing a legitimate domain (openai.com) from an infected device, an attacker can generate and run malicious code, bypassing several standard security checks.

Even though creating polymorphic malware is against OpenAI's terms of service and ChatGPT will refuse to comply with a request to do so if prompted directly, there are countless ways of fooling it into doing it by couching the request in a jailbreak prompt. Cybercriminals constantly think up new prompts to jailbreak ChatGPT so once OpenAI blocks one, they could use another, never really losing the ability to get ChatGPT to give them whatever nefarious content they want.

## Why do cybercriminals sell access to the free version of ChatGPT on the darknet?

They sell OpenAI API keys in bulk so when the first key gets banned (or you hit the limit), the buyer can immediately switch to the next one without losing any time.

> Automatically created accounts with access to the free version of the model are widely sold. Attackers register on the platform using automated tools and fake or temporary details. Such accounts have a limit on the number of API requests and are sold in bundles. This saves time and enables users to immediately switch to a new account as soon as their previous one stops working, for example, following a ban for malicious or suspicious activity.

This is helpful if one's polymorphic malware needs uninterrupted access to the API to regenerate its code and avoid detection by an antivirus. It's also helpful if one is testing new jailbreak prompts.
