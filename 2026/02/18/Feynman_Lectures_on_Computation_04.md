# 4. Coding and Information Theory

This chapter of [Feynman Lectures on Computation](../../../2025/12/05/Feynman_Lectures_on_Computation.md) answered four questions about noise reduction.

## When sending a message over the network (or a bus), why is it a good idea to also include a bit telling us whether the message on the sender end (expressed in binary) was odd or even?

Because by the time it arrives, the physical factors of the transmitter (or the transmitting medium) may have corrupted the message. Such corruptions are so unlikely that we would only expect them to be affecting one bit of the message. This error would be detectable by computing the parity of the binary string (odd or even) and comparing it with the parity reported by the sender. If the parities mismatch, an odd number of bits have been changed in the message (the likeliest number of such corruptions is one, not three, not five, etc).

> This simple check actually enables us to detect any odd number of errors, but not any even number (although as we have ascribed vanishing probability to anything more than a single error, these are assumed not to occur).

Upon discovering a mismatch, the receiver would simply re-request the message.

> All we can do on finding a mistake is have the message sent again. In our case, where we are using a computer, we might simply reboot the machine.

The power of this error-checking algorithm lies in its simplicity: computing binary string parity requires only to count the number of ones in a string modulo 2. If the resulting parity bit was 1, the string was odd. If it was 0, the string was even. 

## How can a sender reconstruct the message sent by a noisy receiver if the bits getting flipped in the message are unpredictable?

The receiver can arrange the message in such a way and introduce so many code bits into it as to make any flips in the data bits completely detectable. Suppose we send 10 bits through a medium/transmitter that is so noisy that we expect 1/3 of those bits to arrive flipped. Shannon's theorem states that if we want to infer which bits were flipped (so we can correct them), we have to send at least 122 code bits in the same message and arrange them in such a way as to make it predictable which of the 10 data bits have been flipped: we need the parity bits on enough of the substrings of the data bits to agree to determine whether a bit co-occurring in them has been flipped.

> M / MC ≤ f(q) = 1 − ( q log₂(1 / q) + (1 − q) log₂(1 / (1 − q)) )

In Shannon's theorem, MC is the length of the coded message, M is the length of the data, and q is the probability of a bit getting flipped by noise. For example, 122 code bits per 10 data bits is the most efficient an error-correct algorithm can get with 1/3 of the bits getting flipped (it is the hard theoretical limit). However, such an algorithm would be too complex to design and/or implement. Real-world algorithms usually rely on 1500 code bits per 10 data bits on such noisy channels. 

> In sending messages from Earth to Jupiter or Saturn, it is not unusual for an error rate q of the order of a third to come through. The upper limit on the efficiency for this, from our table, is 8%; that is, we would have to send about 12 code bits for each data bit. However, to do this would require a prohibitively long MC, so long that it is not practical. In fact, a scheme is used in which about 150 code bits are sent for each data bit!

Imagine a hypercube consisting of n vertices where each vertex corresponds to a binary string of length M. Now imagine a higher-dimensional hypercube consisting of more vertices, corresponding to a binary string of length MC. Suppose one is inscribed in the other, so when a received message corresponds to a vertex on MC, we pick the closest vertex on M.

> We can envisage the space for MC as built out of packed spheres, each of radius e units, centered on acceptable coded message points.

We must design the hypercube MC in such a way that noise can only corrupt the M data bits within the MC bits as to still make the corrupted message fall closest to the original vertex of the M hypercube. A sphere around such a vertex in M must capture every vertex in MC corresponding to every way noise can permute the coded message.

> If we find our received message to lie anywhere within one of these spheres, we know exactly which point cor­responds to the original message.

When there are e errors in a coded message but the acceptable messages are separated by more than 2e, then we can be certain that the original message was the closest acceptable message to the received one.

> Suppose we send an accept­able message M and allow e errors to occur in transmission. The received message M’ will lie at a point in MC e units away from the original. How do we get back from M’ to M? Easy. Because of the separation of d = 2e + 1 we have demanded, M is the closest acceptable message to M’! All other acceptable messages must be at a Hamming distance of at least e+1 from M’.

Mapping transmitted binary strings to higher-dimensional coded strings gives us redundancy: we define a set of acceptable strings, and if the received coded string is not in this set, we simply find the closest one that is. From that, we reconstruct the original data that was sent.

> Whenever we code a message M, we rewrite it into a longer message MC. We can build a message space for MC just as we can for M; of course, the space for MC will be bigger, having more dimensions and points. Clearly, not every point within this space can be associated one-on-one with points in the M-space; there is some redundancy. This redundancy is actually central to coding. e-Error correction involves designing a set of acceptable coded messages in MC such that if, during the transmis­sion process, any of them develops at most e errors, we can locate the original message with certainty. In our geometrical picture, acceptable messages correspond to certain points within the message space of MC; errors make us move to other points, and to have error correction we must ensure that if we find ourselves at a point that does not corre­spond to an acceptable message, we must be able to backtrack, uniquely, to one that does.

## When is something considered informative vs. uninformative?

That depends on the degree of surprise conveyed by the data encountered. Letters are usually uninformative: we can scan a letter for a single word to know what it's about: the presence of the word _sorry_ indicates a rejection letter whereas _pleased_ indicates acceptance.

> The amount of information in a message reflects how much surprise we feel at receiving it. Consider, say, receiving a printed communication from a bookshop, such as: “We are pleased to tell you that the book you ordered is in stock”; or its opposite: “We are sorry to inform you that … is not in stock”; these long messages contain many more symbols but no more information than the simple “Yes” or “No” you could elicit from a shopworker if you called the bookshop direct. Most of the symbols in the printed communications are redundant in any case: you only have to spot the words “pleased” and “sorry” to figure out what they are saying. In this respect, information is as much a property of your own knowledge as anything in the message.

On the other hand, when every sentence in a letter surprises us, we say it's a highly informative letter. By its very nature, every message comes with an element of surprise. So, the more messages there are in a given communication, the more informative it is.

> Receiving the message changes your circumstance from not knowing what it was to now knowing what it is.

The most informative thing in the world is a binary string when it maps to a predefined set of possible messages. With such a mapping, we can receive a message with the least amount of data possible. All N bits in such a binary string are information, not just data.

> If all possible strings are allowable messages, and all are equally likely (which will happen if each bit is equally likely to be 0 or 1), then the information in such a mes­sage will be: I = log₂(2^N) = N.

When you have set up your communication such that binary strings enumerate all possible messages, then upon receiving a given binary string, you know exactly the message it was meant to convey without having to parse it.

## How to compress a corpus of text?

First, find the probabilistic distribution of the substrings in the text.

```
E 0.50 1
THE 0.15 011
AN 0.12 010
O 0.10 000
IN 0.04 01011
R 0.04 01010
S 0.03 01001
PS 0.02 01000
```

Then, divide your text into these substrings and remap them to chunks of bits with the following rule: the more common the substring the shorter its bit chunk.

> The symbol E appears much more often than the others: it turns up 25 times as often as the symbol PS, which takes twice as much effort to write. This symbol system doesn’t look very efficient. Can we write a new code that improves it? Naively, we might think: “Well, we have eight symbols, so let’s just use a three-bit binary code”. But since the E occurs so often, would it not be better to describe it, if we can, by just one bit instead of three? We might have to use more bits to describe the other symbols, but as they’re pretty rare maybe we might still gain something. In fact, it is possible to invent a non-uniform code that is much more efficient, as regards the space taken up by a message, than the one we have. This will be an example of compression of a code. Morse had this idea in mind when he assigned a single “dot” to the common E but “dash dash dot dash” to the much rarer Q.

The assignments to bit chunks can be done by constructing a Huffman coding tree: write down the probabilities in descending order in the first row, combine the lowest two probabilities, re-sort into the next row, etc. When assigning the code to a symbol, retrace its combine actions: at any row, if the symbol's combined probability was the lowest at that row, add 0 to the resulting Huffman code; for second-lowest, add 1; otherwise, ignore the row and proceed to the next one. 

F3

```
00100001101010 (= ANOTHER)
```

> No code word is the prefix of the beginning of any other code word.

The prefix-free property ensures that a flipped bit won't do a frame shift in the entire compressed string.

> An error in position 2 would give us THEOTHER.

That's 01100001101010. But what if the first bit flipped, too? 11100001101010 is EEEOTHER. Fourth? 11110001101010 is EEEEOEER. Third? 11110001101010 is EEPSEER. No matter how much we corrupt the first part of the string, it eventually corrects the frame so the next part of the string would still be correct (ER and everything that would follow it). And if we shift the string by removing the first one, two, three, etc, bits, the end of the message is still correct: PSTHER, EOTHER, OTHER, ... As soon as we encounter a symbol that aligns with the real leaf boundary in the uncorrupted message, the rest of the message will be correct (provided there are no more bit errors following it). However, recoverability alone isn't sufficient for making a usable compression algorithm. The key characteristic is whether it can minimize the length of the compressed message. To do so, we can exploit the fact that, for many messages, if we factor in the preceding characters, the probability of a character occurring next can rise significantly.

> In real, interpretable English, you can’t have every­thing; the number of acceptable words is limited, and the ordering of the letters within them is not random. If you have a “T”, the odds are the next letter is an “H”. It’s not going to be an “X”, and rarely a “J”. Why? The letters are not being used uniformly, and there are very much fewer mes­sages in English than seem available at first sight.

Predictive coding relies on this property. If we have a predictor that accurately predicts most next items in a sequence given the sequence so far, then we can simply encode the positions in text for which the predictor failed. Suppose the predictor fails at position 22 in a string. Then, the compressed message would simply be 10110 (22 in binary), which simply tells us to get the original 21 bytes by running our predictor as is and then flipping the 22nd predicted bit. Or, even better, you assign 21 zeroes followed by a one to a variable-length Huffman code matched to the probability of this sequence occurring and send that.

> You can get pretty close to Shannon’s limit using compres­sion of this sort.

Therefore, if you can find a nearly perfect predictor, it is straightforward to construct a nearly perfect compression algorithm from that.
