# 1. Introduction to Computers

This chapter of [Feynman Lectures on Computation](../../../2025/12/05/Feynman_Lectures_on_Computation.md) finally explained to me how computers, made largely of logic gates, can perform mathematical operations, which operate on numbers, not just the two logical primitives (true and false, or 1 and 0).

## How do computers add numbers?

They perform addition in terms of xor and carry operations on bits.

> A binary addition of 1 and 1 is 10, which is zero if you forget the carry.

The xor gate is an electric circuit that outputs 0 if both inputs are the same, and 1 if they are different. Carry is an electric switch.

## How do computers multiply numbers?

Computers perform the multiplication operation in terms of shift and addition operations on bits.

<img src="https://github.com/user-attachments/assets/1bad1f06-5b94-4af2-95d8-2cc03441e55d" height=200>

If addition can be defined in terms of xor and carry, then multiplication can be defined in terms of shift, xor, and carry. 
