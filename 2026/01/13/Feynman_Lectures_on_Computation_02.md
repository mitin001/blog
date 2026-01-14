# 2. Computer Organization

This chapter of [Feynman Lectures on Computation](../../../2025/12/05/Feynman_Lectures_on_Computation.md) answer it five questions about the applications of logic circuits.

## What does an adder of two numbers look like as a logic circuit? Can it be constructed as a successive application of only one kind logic function on the parameters and their intermediate values, i.e., with many logic gates but all of only one type?

An adder of two bits takes two inputs, A and B, and outputs bits S (sum) and C (carry). S = A XOR B. C = A AND B. Therefore, an adder of two bits can be constructed with two gates: XOR and AND.

Table 1
Figure 2

Once we make 2n-1 such adders, we can join them together to construct an adder for two n-bit numbers. An adder, like any electronic component, can be made from a collection of AND, OR, and NOT gates. That is, the XOR gate can be constructed in terms of the AND, OR, and NOT gates.

FIGURE 2.9

Actually, just the AND and NOT gates are sufficient. The OR gate can be constructed from the AND and NOT gates.

> A OR B is the same as NOT{(NOT A) AND (NOT B)}.

FIGURE 2.8

Actually, just the NAND gate is sufficient. A NAND gate can be used to make both the AND and the NOT gate.

p.33

## What are logic gates made of?

Usually transistors connected to each other with conductors in various arrangements. The arrangement determines its behavior (how it maps the input(s) to the output). A transistor controls the flow of current through it based on the electrical input applied to its gate.

Figure 12

If there's input to the gate, a depletion-type transistor switches off and stops the current flowing through it, which is a NOT gate. Voltage-controlled resistors can also be made from transistors in this way. These circuits cannot be constructed without resistors.

> A transistor is a three-connection device: one input is connected to the gate signal, one to ground, and the other to a positive voltage via a resistor. The central property of the transistor is that if the gate has a distinctly positive voltage, the component conducts, but if the gate is zero or distinctly negative, it does not.

A NAND gate is a depletion-type transistor with two gates, each supplying an argument to the NAND operator. 

Figure 13

## When fetching data from main memory, how does the CPU find the requested memory location? What is the logic circuit between the CPU and main memory?

For simplicity, suppose the memory only has 8 locations which can be represented by lg(8)=3 binary digits (this explanation generalizes to memory of any size that's a power of 2). The CPU sends each binary digit to a decoder, which finds the memory location based on the values of the binary digits.

Figure 16

A decoder looks like a grid: each column is a binary digit in the memory address and each row is a series of AND gates, made at each digit either with the digit itself or its inverse, depending on what the current row is decoding.

p.30

To be able to send to the CPU the data from the given memory location, each row in the decoder connects to a memory cell and then its value sent to the OR gate along with no values (zeros) from the other memory locations. That way, the data is passed along unchanged. The CPU gets the result from the OR gate, which together with the decoder forms a multiplexer.

Figure 17

## What does the logic circuit for converting the wire number to its binary representation look like?

The opposite of a decoder. That is, there are 2^n inputs, n outputs, and the gates at the grid cells are the OR gates.

Figure 24

With a decoder, we take the binary representation of a memory address (e.g., 101) and find the memory location for it (e.g., the 5th location, 101 binary = 5 decimal). With an encoder, we solve the opposite problem: when the signal is sent across the 5th wire, the outputs are {1, 0, 1}.

## What does the logic circuit for a 1-bit memory register look like? 

Suppose conductor Q holds the value of the register: if current flows through Q, then it's 1, otherwise, it's 0. We need a mechanism to set the register value to 1 (set, accomplished by sending current through conductor S) and a mechanism for setting it to 0 (reset, accomplished by sending current through conductor R). So, if S=1, then Q=1, and if R=1, then Q=0.

Table 4

We can design a logic circuit that satisfies this truth table.

Figure 29

This is a flip-flop circuit. 
