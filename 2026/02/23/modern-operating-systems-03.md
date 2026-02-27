# 3. Memory Management

This chapter of [Modern Operating Systems](../../../2026/01/06/modern-operating-systems.md) answered six questions about address spaces.

## Why is it important to study the history of hardware and operating systems?

Because they offer solutions for similar problems that could arise in modern contexts. For example, hardware memory protection schemes that have gone out of style with the introduction of newer technology were brought back once the new technology was proven to be vulnerable to attacks. Whereas in the past hardware protected memory from interloping processes inadvertently accessing another process's memory, nowadays it protects memory from malware actively and adversarily seeking to scour other processes' memory spaces for privileged information.

> Modern Intel x86 processors have advanced forms of memory management and isolation (as we shall see), far more powerful than the simple combination of protection keys and static relocation in the IBM 360. Nevertheless, Intel started adding these exact (and seemingly old-fashioned) protection keys to its CPUs only in 2017, more than 50 years after the first IBM 360 came into use. Now they are touted as an impor- tant security-enhancing innovation.

## Is best fit the best algorithm for picking a hole to fill with a process's data? 

No. Not only is it slow (because it scans the whole memory for holes or requires one to maintain a sorted list of holes), it also introduces unusable segments into memory.

> Best fit is slower than first fit because it must search the entire list every time it is called. Somewhat surprisingly, it also results in more wasted memory than first fit or next fit because it tends to fill up memory with tiny, useless holes.

The opposite of best fit, worst fit, is not optimal either. Even if it doesn't introduce as many unusable segments, it is still slow and tests poorly in practice.

> To get around the problem of breaking up nearly exact matches into a process and a tiny hole, one could think about worst fit, that is, always take the largest available hole, so that the new hole will be big enough to be useful. Simulation has shown that worst fit is not a very good idea either.

Thus, the best algorithm for memory allocation is first fit.

## Why are page sizes always chosen to be the power of 2?

Because this way, the math the MMU must do to compute the memory location of the page in physical memory is does not involve carry operations. It is simply a replacement of a prefix in a memory address.

<img width="863" height="956" alt="17719122999446115723990988736065" src="https://github.com/user-attachments/assets/22a86fc9-6154-432c-acaa-63dd0e6cc77a" />

The higher-order bits determine the new page starting location (they are mapped to the page start in the physical memory by the page table), and the rest of the bits are the offset from the starting location, which are the same because the page size in virtual memory matches the page size in physical memory. 

## Why is it guaranteed that the second-chance page replacement algorithm always terminates?

Because it falls back on FIFO, which always terminates.

> What second chance is looking for is an old page that has not been referenced in the most recent clock interval. If all the pages have been referenced, second chance degenerates into pure FIFO.

If at time 20, the program needs to evict a page and finds that page A, which has been loaded at time 0, has its R bit set (indicating that it was recently used), A is moved to the top of the list, before the most recently used page (H), but with its R bit cleared. This way, if the algorithm goes through the rest of the pages and all of them have their R bits set as well, it will eventually run into A again, but this time, its R bit would show up as cleared, and so it will be evicted by the algorithm.

<img width="864" height="305" alt="17719123388521653306020029841681" src="https://github.com/user-attachments/assets/bc7fa0cc-c0b4-4c35-81d2-97c6237bce8d" />

The second-chance algorithm does not even need the overhead of moving pages in a list if it incorporates the clock metaphor: on page fault, the hand of the clock moves through pages and clears their R bits until it finds one the R bit of which is already 0, at which point it evicts that page. This is called the clock page replacement algorithm.

<img width="864" height="454" alt="17719123544221703660357791275596" src="https://github.com/user-attachments/assets/c2bb3c8c-76bd-4aef-b2c3-a9452315a3b8" />

## Is LRU the optimal page replacement algorithm? 

No, LRU evicts the least recently used page. The optimal algorithm would evict the page whose next use will be farthest in the future. These are not the same attribute. 

> In the abstract, the basic page replacement algorithms (FIFO, LRU, optimal) are identical except for the attribute used for selecting the page to be replaced.

FIFO is not the optimal algorithm either because it evicts the oldest page; this strategy is even further away from optimality than evicting the least recently used page.

## How do hackers attack memory?

They typically try to gain unauthorized access to privileged data in memory. One way they do it is by examining the raw bytes of the parts of memory that have been marked as free but have not yet been overwritten. If the memory page has been used by a sensitive program to store sensitive data, it will still be there, possibly no longer protected by the operating system. It is also a window into how a privileged process manages its memory.

> Reducing the memory footprint of a system by means of memory deduplication turns out to be a highly security sensitive operation. Who knew? For instance, attackers may detect that a page has been deduplicated and thus learn what another process has in its address space.

Another attack involves corrupting parts of memory and seeing if a program leaks sensitive data as a result. Hackers assess performance optimizations for vulnerabilities (e.g., the Meltdown vulnerability). When they succeed at exploiting them, they force chip manufacturers to remove those optimizations, thereby making computers slower for the rest of us.

> Where the Linux kernel was originally mapped into the address space of every process as a measure to speed up system calls (by obviating the need to change page tables for a system call), Meltdown required strict page table isolation. As it made the context switch much more expensive, the Linux developers were furious with Intel.
