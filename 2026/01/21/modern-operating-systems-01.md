# 1. Introduction

This chapter of [Modern Operating Systems](../../../2026/01/06/modern-operating-systems.md) answered eleven questions about computer hardware and interacting with it, how it was done in the past, and how it is done today.

## Has the gender disparity always been so pronounced in programming jobs?

Not at first. When Charles Babbage's mechanical computer (arguably the first computer ever invented) needed software, a woman was offered the job.

> He hired a young woman named Ada Lovelace, who was the daughter of the famed British poet Lord Byron, as the world’s first programmer. The programming language Ada is named after her.

At least back then, networking seemed to be more important than gender, at least judging by the sample size of one (albeit a prominent one).

## What is spooling?

Storing a job on a queue for later processing. This term was invented when there was a need for it—in early batch-processing computer systems.

> The ability to read jobs from cards onto the disk as soon as they were brought to the computer room. Then, whenever a running job finished, the operating system could load a new job from the disk into the now-empty partition and run it.

Spooling automated the need for a human operator to load a program into the computer when the old one finished—the computer simply moved on to the next program in the preloaded batch. In coming up with the term, engineers looked at tape on a _spool_ and invented an abbreviation that spelled it out.

> Simultaneous Peripheral Operation On Line.

So in our time, when you're sending a job to the printer, you're _spooling_ it, if we're to use operating system terminology. It would be imprecise to say that the job is _cached_ on disk until it is processed by the printer. _Caching_ doesn't come with a guarantee of being processed and in the order in which it was received, but _spooling_ does. At least, in theory.

> In theory, theory and practice are the same; in practice, they are not.

Yogi Berra got that right. One needs to look only at an ocean of questions from exasperated users debugging their printer spoolers to understand that a simple idea in theory can turn into a generator of endless frustration in practice.

## How does a computer operate?

Main memory is like a large computer program: every memory location is like a line of code. The CPU goes through the memory line by line and performs the basic commands using the circuitry that surrounds it.

> The basic cycle of every CPU is to fetch the first instruction from memory, decode it to determine its type and operands, execute it, and then fetch, decode, and execute subsequent instructions.

Sometimes, the instructions require the CPU to jump to non-adjacent memory locations or edit memory (so next time it encounters the same location, it will execute different code). This is what makes a computer so flexible in its applications. It also makes it fast: the CPU can perform millions of simple operations per second. CPU designers also go to great lengths to ensure the CPU doesn't sit idle if it doesn't have to. They invent things like hyperthreading.

> If one of the processes needs to read a word from memory (which takes many clock cycles), a multithreaded CPU can just switch to another thread.

When an instruction takes longer to execute than to fetch, one unit in a CPU can get busy fetching the next instruction while the other is continuing to execute the first one.

> To improve performance, CPU designers have long abandoned the simple model of fetching, decoding, and executing one instruction at a time. Many modern CPUs have facilities for executing more than one instruction at the same time. For example, a CPU might have separate fetch, decode, and execute units, so that while it is executing instruction n, it could also be decoding instruction n + 1 and fetching instruction n + 2. Such an organization is called a pipeline.

To achieve any level of complexity, a CPU needs to manage its internal state, and that requires storage. Using main memory for such storage wouldn't be efficient, so the CPU has its own, faster storage system: the registers.

> Because accessing memory to get an instruction or data word takes much longer than executing an instruction, all CPUs contain registers inside to hold key variables and temporary results.

It gets complex fast. For example, a superscalar CPU keeps track of incoming instructions in buffers and feeds them to its subunits according to type and availability.

> Multiple execution units are present, for example, one for integer arithmetic, one for floating-point arithmetic, and one for Boolean operations. Two or more instructions are fetched at once, decoded, and dumped into a holding buffer until they can be executed. As soon as an execution unit becomes available, it looks in the holding buffer to see if there is an instruction it can handle, and if so, it removes this instruction from the buffer and executes it.

Sequential execution of instructions by the CPU has been an illusion for a long time, just as multiple programs executing on a computer at once is an illusion. The operating system manages the CPU to maintain the latter illusion. To do so, it must back up the state of the registers every time it switches to another program and then restore it when it switches back.

> When time multiplexing the CPU, the operating system will often stop the running program to (re)start another one. Every time it stops a running program, the operating system must save all the registers so they can be restored when the program runs later.

## What is the difference between parallelism and multithreading? Why is it important for an operating system to distribute work across processor cores and not threads?

Since a core consists of multiple threads, a core-unaware distribution mechanism could assign two processes to different threads on the same core.

> Each thread appears to the operating system as a separate CPU. Consider a system with two actual CPUs, each with two threads. The operating system will see this as four CPUs. If there is only enough work to keep two CPUs busy at a certain point in time, it may inadvertently schedule two threads on the same CPU, with the other CPU completely idle. This is far less efficient than using one thread on each CPU.

Multithreading is not true parallelism; it is an illusion of it: the core switches between the threads quickly to repurpose some of the time it would've sat idly waiting for execution results for pre-fetching instructions for the different thread. The total work will not be done in half the time. Meanwhile, assigning two processes to two different cores will ensure the total work will be done in half the time.

## How to write a program that takes advantage of the GPU?

A GPU is a graphical processing unit, but it can be used for non-graphical applications, too. It is a multicore processor.

> With, literally, thousands of tiny cores. They are very good for many small computations done in parallel, like rendering polygons in graphics applications.

Whereas modern CPUs are split into several independent cores, GPUs are split into thousands. The cores are much smaller and can perform much simpler computations, but their sheer numbers make them powerful. If you can modularize your program into many series of thousands of very simple computations that can all be done in parallel, then you'll be able to achieve supercomputer-level performance with a regular, cheap GPU. That is, it'll perform just as fast as had a computer with thousands of CPU cores run an original version of it (one where the entire chunk could be split into thousands of complex tasks rather than each of the complex tasks also being split into simple independent computations).

## How does the hardware protect against unauthorized privilege escalation?

If the PSW register in the CPU is set to 1 during the execution of the instruction, then the CPU executes it regardless of the type of instruction.

> A bit in the PSW controls the mode. When running in kernel mode, the CPU can execute every instruction in its instruction set and use every feature of the hardware.

If, on the other hand, PSW=0 and the instruction is privileged, the CPU does not execute it.

> All instructions involving I/O and memory protection are disallowed in user mode.

For this reason, a user program cannot execute any instruction that requires privilege escalation in _user mode_. It must call a procedure provided by the operating system kernel (only they can set PSW=1, i.e., run in _kernel mode_). So, the operating system manages how these calls are made and denies access to them without proper authorization.

## Why can virtual machines not run on some CPUs?

Because a hypervisor is a user-mode program, so when the guest OS running in it attempts to run kernel-mode instructions, the non-virtualizable CPU treats it as unauthorized privilege escalation.

> When an operating system running on a virtual machine (in user mode) executes a privileged instruction, such as modifying the PSW or doing I/O, it is essential that the hardware trap to the virtual-machine monitor so the instruction can be emulated in software. On some CPUs—notably the Pentium, its predecessors, and its clones—attempts to execute privileged instructions in user mode are just ignored. This property made it impossible to have virtual machines on this hardware.

Attempts to make virtual machines run on non-virtualizable CPUs have been made, but even when they were successful, the performance penalties incurred rendered them useless.

## Why are operating systems usually written in C?

Because it doesn't have unpredictable features like garbage collection.

> All storage in C is either static or explicitly allocated and released by the programmer, usually with the library functions malloc and free. It is the latter property—total programmer control over memory—along with explicit pointers that makes C attractive for writing operating systems. Operating systems are basically real-time systems to some extent, even general-purpose ones. When an interrupt occurs, the operating system may have only a few microseconds to perform some action or lose critical information. Having the garbage collector kick in at an arbitrary moment is intolerable.

Whereas it takes more work to manage memory in C than in Java, this comes with finer control over memory, which is something a reliable operating system must have.

## What is Moore's law? 

An observation of the pace of innovation in CPU design. 

> An observation by Intel cofounder Gordon Moore of how fast process engineers at the semiconductor companies are able to shrink their transistors.

Engineers have been able to find new ways of fitting more transistors on their chips consistently for several decades.

> The number of transistors on a chip doubles every 18 months.

We're almost at a point where the transistors are packed so closely to each other that quantum laws are starting to interfere with their placement (the same quantum laws that prevent electrons from coming too close to atomic nuclei). Will the CPU designers find a way around that so the Moore's law continues to hold? Can Moore's law defeat the laws of quantum mechanics?

## What is the difference between L1 and L2 caches?

How long it takes to retrieve the data.

> Access to the L1 cache is done without any delay, whereas access to the L2 cache involves a delay of several clock cycles.

And it takes even more clock cycles to retrieve data from further away from the CPU. This is why CPU designers have figured out ways of keeping the CPU busy executing whatever instructions it can (or preparing for them) while waiting for data: so as to not waste the precious clock cycles.

## What does SATA stand for?

Serial advanced technology attachment. Therein lies a lesson for putting words like "advanced" into a technology, which like any technology, is destined for obsolescence.

> An adjective like “advanced” should be used with great care, or you will look silly 40 years down the line.
