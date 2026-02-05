# 3. The Theory of Computation

This chapter of [Feynman Lectures on Computation](../../../2025/12/05/Feynman_Lectures_on_Computation.md) answered six questions about mathematics in the age of machines.

## Why did it take so long to find algorithms for integration and Eucledean geometry?

Because people only started thinking about mathematics in terms of procedures with the advent of computers. Until then, the framing was philosophical.

> Converting questions to effective procedures is pretty much equivalent to getting them into a form whereby computers can handle them, and this is one of the reasons why the topic has attracted so much attention of late (and why, for example, the notion of effective procedures in integration has only recently been addressed and solved). When mathematicians first addressed these problems, their interest was more general than the practical limits of computation; they were interested in principle with what could be proved.

The lesson is that when you have a hard time solving a problem, try reframing it. You may happen upon a frame from which the solution is obvious.

## How is it possible that any Turing machine, no matter how complex, can be simulated with a six-state universal Turing machine?

Because any TM can be described completely with a set of quintuples: state, new state, read, write, and direction of motion. UTM stores the quintuples on part of the tape, reads them, and performs the state transitions accordingly on the adjacent part of the tape.

> It is surprising that such a general-purpose machine should require so few parts for its description; surely a machine that can do everything should be enormously complicated? The surprising answer is that it’s not!

The reason we build specialized TMs and not always rely on a UTM is performance. By constructing a complicated web of states and transitions in the TM itself, we can avoid having it read the quintuples off the tape. This way the head won't keep zigzagging between the instruction and execution portion. However, the reality of computation today is more like a UTM: a CPU reads instructions off memory and stores data in adjacent regions of the same memory.

## Why is it impossible to devise a Turing machine that can accurately predict whether another Turning machine will halt or loop forever?

Suppose we have devised such a TM. That is, imagine a TM D that accepts another TM as input and outputs whether it halts or not. Then, imagine a TM Z that accepts TM T as input, asks D whether T halts, and does the opposite (loops forever if D says that T halts, or halts if D says T loops forever). If we give Z its own description as input, what happens? That's undefined behavior because D cannot exist. It's impossible for D to predict whether any TM halts when there can be a TM that could call it with itself and then do the opposite. No matter how you devise D, its predictions will always be unreliable.

## Why are real numbers uncountable?

Because whatever way you devise to count all real numbers (map them to integers), there will always be a real number that's unaccounted for. Suppose we have devised such a procedure.

```
1    0.124
2    0.015
3    0.53692
4    0.8003444
5    0.334105011
6    0.3425...
```

Let's take a digit after the decimal from each row going diagonally to obtain 0.11630... Let's invent some mapping for the digits (e.g., +1 on each digit) to obtain 0.22741... This number will not have been mapped to integers. We can use diagonalization to find infinitely many such numbers—counterexamples.

## What is the simplest program for deciding whether a given number is divisible by some number y if the acceptable error rate for such a program is 1/y?

Simply have it respond with _no_ on any input.

> If y is big enough, the odds are in my favor that I am right: to be precise, the odds are 1 in y that a randomly chosen number is divisible by y. The principle here is that you can know a lot more than you can prove! Unfortunately, it is also possible to think you know a lot more than you actually know. Hence the frequent need for proof.

## How to quickly determine whether a number (with a small number of digits) is prime?

> An effective procedure for this might involve taking all prime numbers up to n^1/2 and seeing if any divide n; if not, n is prime.

For example, we can quickly see that 167 is prime because it is not divisible by 2, 3, 5, 7, or 11. The next prime number is 13, and there's no point in checking that because 167 < 13^2.
