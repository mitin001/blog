# 2. Computer Organization

This chapter of [Feynman Lectures on Computation](../../../2025/12/05/Feynman_Lectures_on_Computation.md) answered five questions about applications of logic circuits.

## What does an adder of two numbers look like as a logic circuit? Can it be constructed as a successive application of only one kind logic function on the parameters and their intermediate values, i.e., with many logic gates but all of only one type?

An adder of two bits takes two inputs, A and B, and outputs bits S (sum) and C (carry). S = A XOR B. C = A AND B. Therefore, an adder of two bits can be constructed with two gates: XOR and AND.

<img width="864" height="402" alt="17683787560473417017218168615847" src="https://github.com/user-attachments/assets/2ac1a3a2-d226-4849-9d30-e8009c06c927" />

<img width="200" alt="17683749971478206496679556961864" src="https://github.com/user-attachments/assets/92323365-ff38-45e6-8e89-368b19d9d2eb" />

Once we make 2n-1 such adders, we can join them together to construct an adder for two n-bit numbers. An adder, like any electronic component, can be made from a collection of AND, OR, and NOT gates. That is, the XOR gate can be constructed in terms of the AND, OR, and NOT gates.

<img width="2023" height="565" alt="17683751125896556272781544646352" src="https://github.com/user-attachments/assets/665565e4-705f-4c50-a879-8ec56eac9585" />

Actually, just the AND and NOT gates are sufficient. The OR gate can be constructed from the AND and NOT gates.

> A OR B is the same as NOT{(NOT A) AND (NOT B)}.

<img width="1433" height="249" alt="17683751445659135873912759114098" src="https://github.com/user-attachments/assets/6d6342cb-d666-4653-bca9-f93d5cadf877" />

Actually, just the NAND gate is sufficient. A NAND gate can be used to make both the AND and the NOT gate.

<img width="2378" height="233" alt="17683753954968378986746911147099" src="https://github.com/user-attachments/assets/5e1144df-9c7b-4750-b006-50671f838ccd" />

## What are logic gates made of?

Usually transistors connected to each other with conductors in various arrangements. The arrangement determines its behavior (how it maps the input(s) to the output). A transistor controls the flow of current through it based on the electrical input applied to its gate.

<img width="1433" height="1043" alt="17683751755967862092754668793180" src="https://github.com/user-attachments/assets/a61cd9b7-3f32-44c4-bfea-f41cb8544690" />

If there's input to the gate, a depletion-type transistor switches off and stops the current flowing through it, which is a NOT gate. Voltage-controlled resistors can also be made from transistors in this way. These circuits cannot be constructed without resistors.

> A transistor is a three-connection device: one input is connected to the gate signal, one to ground, and the other to a positive voltage via a resistor. The central property of the transistor is that if the gate has a distinctly positive voltage, the component conducts, but if the gate is zero or distinctly negative, it does not.

A NAND gate is a depletion-type transistor with two gates, each supplying an argument to the NAND operator. 

<img width="1924" height="1427" alt="17683751893539081541308241929796" src="https://github.com/user-attachments/assets/510cf11f-b8df-4163-9983-2b5c6ea9cc1d" />

## When fetching data from main memory, how does the CPU find the requested memory location? What is the logic circuit between the CPU and main memory?

For simplicity, suppose the memory only has 8 locations which can be represented by lg(8)=3 binary digits (this explanation generalizes to memory of any size that's a power of 2). The CPU sends each binary digit to a decoder, which finds the memory location based on the values of the binary digits.

<img width="2140" height="1072" alt="17683752082183710129011784333062" src="https://github.com/user-attachments/assets/aac87600-9be0-4ffc-a817-ee8861fdd4e2" />

A decoder looks like a grid: each column is a binary digit in the memory address and each row is a series of AND gates, made at each digit either with the digit itself or its inverse, depending on what the current row is decoding.

<img width="1550" height="517" alt="17683752264838949118517786753344" src="https://github.com/user-attachments/assets/a8761aa0-3714-42e2-9f62-fd419ac4faad" />

To be able to send to the CPU the data from the given memory location, each row in the decoder connects to a memory cell and then its value sent to the OR gate along with no values (zeros) from the other memory locations. That way, the data is passed along unchanged. The CPU gets the result from the OR gate, which together with the decoder forms a multiplexer.

<img width="1787" height="691" alt="17683752693234134784253088872058" src="https://github.com/user-attachments/assets/438e06f0-ccd7-4f71-afab-a26ad38fc170" />

## What does the logic circuit for converting the wire number to its binary representation look like?

The opposite of a decoder. That is, there are 2^n inputs, n outputs, and the gates at the grid cells are the OR gates.

<img width="2142" height="959" alt="17683753258002726947140306768625" src="https://github.com/user-attachments/assets/f2d7f0d3-2555-4926-a4e5-52424afff8ed" />

<img width="1195" height="738" alt="17683753472379134208865691880758" src="https://github.com/user-attachments/assets/834fc6ac-eb92-4f5f-939c-0a6911ea0337" />

With a decoder, we take the binary representation of a memory address (e.g., 101) and find the memory location for it (e.g., the 5th location, 101 binary = 5 decimal). With an encoder, we solve the opposite problem: when the signal is sent across the 5th wire, the outputs are {1, 0, 1}.

## What does the logic circuit for a 1-bit memory register look like? 

Suppose conductor Q holds the value of the register: if current flows through Q, then it's 1, otherwise, it's 0. We need a mechanism to set the register value to 1 (set, accomplished by sending current through conductor S) and a mechanism for setting it to 0 (reset, accomplished by sending current through conductor R). So, if S=1, then Q=1, and if R=1, then Q=0.

<img width="864" height="516" alt="17683787825182402948973765240312" src="https://github.com/user-attachments/assets/d2c457b8-0e02-469a-81f3-e55750c66070" />

We can design a logic circuit that satisfies this truth table.

<img width="1776" height="825" alt="17683754332067897193342813138018" src="https://github.com/user-attachments/assets/d2c9996c-e8a2-4feb-b1d1-91ddf9751234" />

This is a flip-flop circuit. 
