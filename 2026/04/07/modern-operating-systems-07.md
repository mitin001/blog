# 7. Virtualization and the Cloud

This chapter of [Modern Operating Systems](../../../2026/01/06/modern-operating-systems.md) answered eight questions about virtual machines.

## Is the Linux stack more stable when it runs on the cloud than from home?

Yes, at least for the fact that machines in cloud data centers run hypervisors between their hardware and operating system layers. Operating systems are far too complex to be allowed direct access to hardware; they should be managed with hypervisors if we want cloud-level stability.

> Most service outages are due not to faulty hardware, but to ill-designed, unreliable, buggy, and poorly configured software, emphatically including operating systems. With virtual machine technology, the only software running in the highest privilege mode is the hypervisor, which has two orders of magnitude fewer lines of code than a full operating system, and thus two orders of magnitude fewer bugs. A hypervisor is simpler than an operating system because it does only one thing: emulate multiple copies of the bare metal (most commonly the Intel x86 architecture, although ARM is becoming popular in data centers also).

Of course, cloud computing providers rely on hypervisors not for the increased stability but to allow their machines to run multiple operating systems at a time to better support the needs of their clients (and to isolate them from each other in a multi-tenant architecture); the better stability is just a bonus feature of this design. 

## How does UNIX perform OS-level virtualization?

With the chroot (change root) system call.

> The system call takes as its single argument a path name, for instance /home/hjb/my_new_root, which is where it will create a new ‘‘root’’ directory for the current process and all of its children. Thus, when the process reads a file /README.txt (a file in the root directory), it really accesses /home/hjb/my_new_root/README.txt. In other words, the operating system has created a separate environment on disk to which the process is confined. It cannot access files from directories other than those in the subtree below the new root (and we had better make sure that all files the process ever needs will be in this subtree, because they are literally all it can access).

A process is started in the host OS root and then changes its root to a different directory to isolate itself from the host OS. It was eventually recognized that isolation in domains beyond the file system was needed for true containerization.

> In 2000, Poul-Henning Kamp and Robert Watson extended the chroot isolation in the FreeBSD operating system to create what they referred to as FreeBSD Jails.

Thanks to FreeBSD Jails, we now have the likes of Docker allowing us to create virtual network interfaces, VCPUs, and VRAMs, and assign them to lightweight operating systems running in isolated containers.

> Jails had their own file system name spaces, their own IP addresses, their own (limited) root processes, etc. Their elegant solution was hugely influential and soon similar features appeared in other operating systems, often partitioning even more resources, such as memory or CPU usage.

## How did the VMware hypervisor isolate user processes from the guest OS and the guest OS from the hypervisor on x86 pre-VT?

It took advantage of the CPU's four protection rings by placing the hypervisor in ring 0, the guest OS in ring 1, and user processes in ring 3.

<img width="400" alt="17756184475496951795741403299588" src="https://github.com/user-attachments/assets/f1ea7e88-fb16-4092-9310-9dd3999c1523" />

Whereas a regular OS kernel has privileged access to hardware and allows user processes to trap into the kernel when needed, an OS running on a hypervisor needs to propagate kernel traps another layer—into the hypervisor ring. For each basic block (sequence of instructions) in the guest OS kernel, VMware hypervisor detects any that would behave differently if ran in the true privileged mode on the hardware (sensitive instructions) and replaces them with hypervisor procedures through binary translation.

> The kernel is privileged relative to the user processes and any attempt to access kernel memory from a user program leads to an access violation. At the same time, the guest operating system’s privileged instructions trap to the hypervisor. The hypervisor does some sanity checks and then performs the instructions on the guest’s behalf.

Hypervisors emulate operating system kernels.

> Sensitive instructions in the guest kernel are replaced by calls to procedures that emulate these instructions. No sensitive instructions issued by the guest operating system are ever executed directly by the true hardware. They are turned into calls to the hypervisor, which then emulates them.

## Why is trapping to the kernel considered to have a large performance penalty?

Because the longer a user-space procedure runs uninterrupted, the better it adapts its environment for itself, caching frequently used memory pages and disk blocks and making itself more predictable to the system. Kernel traps cause the system to abandon all the progress made toward adapting to the running process.

> They ruin CPU caches, TLBs, and branch prediction tables internal to the CPU.

Emulating traps to the kernel in user space can therefore be a performance optimization.

> Some type 1 (and type 2) hypervisors do binary translation for performance reasons, even though the software will execute correctly without it.

Don't be surprised if a program runs much faster in a guest OS than an OS running directly on top of the hardware, especially if such a program frequently traps into the kernel.

> Suppose, for instance, that the guest operating system disables hardware interrupts using the CLI instruction (‘‘clear interrupts’’). Depending on the architecture, this instruction can be very slow, taking many tens of cycles on certain CPUs with deep pipelines and out-of-order execution. It should be clear by now that the guest’s wanting to turn off interrupts does not mean the hypervisor should really turn them off and affect the entire machine. Thus, the hypervisor must turn them off for the guest without really turning them off. To do so, it may keep track of a dedicated IF (Interrupt Flag) in the virtual CPU data structure it maintains for each guest (making sure the virtual machine does not get any inter- rupts until the interrupts are turned off again). Every occurrence of CLI in the guest will be replaced by something like ‘‘VirtualCPU.IF = 0’’, which is a very cheap move instruction that may take as little as one to three cycles. Thus, the translated code is faster.

In a way, the hypervisor imposes the microkernel architecture on the system.

> By removing all the sensitive instructions from the operating system and just having it make hypercalls to get system services like I/O, we have turned the hypervisor into a microkernel.

The reason adding a hypervisor layer between the hardware and the OS might improve performance is that it significantly reduces the amount of code that runs against bare metal. The fewer lines of code there are in a program, the less space there is for bugs.

> The program running in kernel mode on the bare hardware should be small and reliable and consist of thousands, not millions, of lines of code.

## How does the hypervisor isolate one guest OS from another in physical memory?

This is a tricky problem because an OS maps physical memory pages to its virtual pages by simply writing to memory (without having to make system calls and therefore without notifying the hypervisor). One way the hypervisor can solve this problem is making the page with the guest OS page table read-only. This will force all attempts by the guest OS at modifying the memory to result in the hypervisor being notified of them (because it handles sensitive instructions).

> Keep track of which page in the guest’s virtual memory contains the top-level page table. It can get this information the first time the guest attempts to load the hardware register that points to it because this instruction is sensitive and traps. The hypervisor can create a shadow page table at this point and also map the top-level page table and the page tables it points to as read only. A subsequent attempts by the guest operating system to modify any of them will cause a page fault and thus give control to the hypervisor, which can analyze the instruction stream, figure out what the guest OS is trying to do, and update the shadow page tables accordingly.

This design adds overhead to each page table modification, which significantly reduces performance of the guest OS. For this reason, as long as there is hardware support for them, nested page tables are the preferred way of isolating guest OS memory.

## How does the hypervisor reclaim memory from one guest OS to give to another?

It installs the balloon driver into the guest OS, which can then allocate pages from within the guest OS. The OS will respond to this increased memory pressure by evicting the least important pages from memory.

> The balloon module may inflate at the hypervisor’s request by allocating more and more pinned pages, and deflate by deallocating these pages. As the balloon inflates, memory scarcity in the guest increases. The guest operating system will respond by paging out what it believes are the least valuable pages—which is just what we wanted. Conversely, as the balloon deflates, more memory becomes available for the guest to allocate. In other words, the hypervisor tricks the operating system into making tough decisions for it.

Without ballooning, the hypervisor itself would have to decide which pages to evict on behalf of the guest OS, and it would invariably make much less informed decisions (since it doesn't control the guest OS processes directly), which would degrade performance (e.g., it could evict a page that would then be immediately paged back in because it was in use by a process).

## How to get an operating system to use the hardware for which there are no drivers?

Use a hypervisor. If the OS doesn't support the physical device, it might still be able to support the virtual version of said device provided to it by the virtual machine.

> If the actual disk is some brand-new high-performance disk (or RAID) with a new interface, the hypervisor could advertise to the guest OS that it has a plain old IDE disk and let the guest OS install an IDE disk driver. When this driver issues IDE disk commands, the hypervisor converts them into commands to drive the new disk. This strategy can be used to upgrade the hardware without changing the software. In fact, this ability of virtual machines to remap hardware devices was one of the reasons VM/370 became popular: companies wanted to buy new and faster hardware but did not want to change their software. Virtual machine technology made this possible.

Suppose you bought a WiFi adapter you wanted to use with Linux, but there are no drivers for it, so it doesn't work. The same device might work plug-and-play on Windows. If that's the case, one solution would be to run Linux in a type 2 hypervisor running on top of Windows. This way, the guest Linux will have WiFi connectivity from the device that could never provide it to the same version of Linux had it run directly on the hardware.

## How to move a virtual machine to different hardware without downtime?

Copy all the memory pages even as they're being modified by the live VM. After the bulk of the memory is copied, cut over to the new VM, recopy the pages that have been modified since the copying has started, and resume service. Downtime between the cutover and the resumption of service cannot be avoided but it can be minimized to the point where it's not noticable.

> Most memory pages are not written much, so copying them over is safe. Remember, the virtual machine is still running, so a page may be modified after it has already been copied. When memory pages are modified, we have to make sure that the latest version is copied to the destination, so we mark them as dirty. They will be recopied later. When most memory pages have been copied, we are left with a small number of dirty pages. We now pause very briefly to copy the remaining pages and resume the virtual machine at the new location. While there is still a pause, it is so brief that applications typically are not affected. When the downtime is not noticeable, it is known as a seamless live migration.
