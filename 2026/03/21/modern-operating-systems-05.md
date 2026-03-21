# 5. Input/Output

This chapter of [Modern Operating Systems](../../../2026/01/06/modern-operating-systems.md) answered fourteen questions about how operating systems interact with devices.

## What's the difference between interrupts, traps, exceptions, and faults?

Traps and exceptions are both interrupts. The difference is how they are triggered: a system call deliberately traps into the operating system kernel whereas exceptions are errors encountered by programs. Not every exception involves a recoverable error; a fault is an exception that involves a recoverable error.

> We generally use trap to refer to a deliberate action by the program code, for instance, a trap into the kernel for a system call. A fault or exception is similar, except that it is generally not deliberate. For instance, the program may trigger a segmentation fault when it tries to access memory that it is not allowed to access or wants to learn what 100 divided by zero is.

Hardware interrupts are not really traps so we refer to them as simply hardware interrupts. 

> A device such as printer or a network sends a signal to the CPU.

## Is a superscalar CPU always faster than a regular one?

Until it has to do an imprecise interrupt, at which point it discovers that the last n instructions are in various states of incompletion, so it must do the work of saving and then restoring the large, complex state describing the incomplete instructions and thus appear slower than it is.

<img width="300" alt="17740701472904104349620473241662" src="https://github.com/user-attachments/assets/1400d057-7910-45b4-82c2-089b504161c4" />

> Machines with imprecise interrupts usually vomit a large amount of internal state onto the stack to give the operating system the possibility of figuring out what was going on. The code necessary to restart the machine is typically exceedingly complicated. Also, saving a large amount of information to memory on every interrupt makes interrupts slow and recovery even worse. This leads to the ironic situation of having very fast superscalar CPUs sometimes being unsuitable for real-time work due to slow interrupts.

Increased complexity also leads to security vulnerabilities. Even as the CPU works diligently to undo transient instructions to service the interrupt, pieces of their data may still be discoverable by attackers.

> They leave traces deep in the micro-architecture (where we find the cache and the TLB and other components) which an attacker may use to leak sensitive information.

Another way to do an imprecise interrupt is just to delay the interrupt until all the started instructions finish.

> CPU architects know that operating system writers hate imprecise interrupts. One way to please the OS folks is for the CPU to stop issuing new instructions when an interrupt is signaled, but allow all the instructions currently being executed to finish, then force the interrupt.

However, this can make interrupt delays intolerably long and unpredictable, so this is only reserved for systems that can tolerate them. The delays of instruction rollbacks in precise interrupts are, on the other hand, shorter and more predictable, so this is the mainstream interrupt scheme in present-day CPU architecture.

## Why does the operating system first copy the string to be printed into the kernel space rather than simply print it from the user space?

To prevent the printer from printing garbled data by ensuring it's not printing from a memory location actively being modified by user. The kernel space is the isolated staging location for the data to be sent to the device.

> It is more easily accessed (because the kernel may have to change the memory map to get at user space) and also safe from modification by the user process.

## Why do some devices require two buffers in the kernel space? 

Double buffering allows one buffer to be copied into user space while another one is still being filled up. This way, the driver doesn't have to worry about copying a buffer that's being modified.

> The two buffers take turns: while one is being copied to user space, the other is accumulating new input.

If the user space is the final destination, why does the device buffer into the kernel space and not directly into the user space? Because the memory of the process requesting the data from the device may be paged out.

> What happens if the buffer is paged out when a character arrives? The buffer could be locked in memory, but if many processes start locking pages in memory willy nilly, the pool of available pages will shrink and performance will degrade.

Why bother with buffering at all? Because issuing a hardware interrupt for every incoming character from the device would slow the system to a crawl.

## What is a circular buffer?

A way to keep the system from copying the buffer data that hasn't finished writing without resorting to double buffering. In a circular buffer, the data is written to the end of the buffer but read from the beginning of it. This buffering scheme makes sense for situations in which the reader can be kept from reading past the end of the buffer.

> It consists of a region of memory and two pointers. One pointer points to the next free word, where new data can be placed. The other pointer points to the first word of data in the buffer that has not been removed yet. In many situations, the hardware advances the first pointer as it adds new data (e.g., just arriving from the network) and the operating system advances the second pointer as it removes and processes data. Both pointers wrap around, going back to the bottom when they hit the top.

## Why does a network packet have to go through a network controller before getting onto the wire rather than being copied from main memory directly?

The network controller ensures the packet gets onto the network at a uniform speed, which is a requirement for correctly encoding the data in the packet.

> Once a packet transmission has been started, it must continue at a uniform speed. The driver cannot guarantee that it can get to memory at a uniform speed because DMA channels and other I/O devices may be stealing many cycles. Failing to get a word transmitted on time would ruin the packet. By buffering the packet inside the controller, this problem is avoided.

Had main memory put the packet onto the wire directly, the cycle stealing by everything else sharing the main memory bus would make it impossible for the receiver to decode it. The network controller effectively filters out (absorbs, buffers) the stutters and pauses in the transmitted data at the cost of the time taken to sequentially copy the data from the kernel space onto the controller and then from the controller onto the wire. Before the data in the user space of one host gets into the user space of another through the network, it must be copied at last five times: into the sender's kernel space buffer, the sender's controller buffer, the receiver's controller buffer, the receiver's kernel space buffer, and finally the receiver's user space buffer.


<img width="400" alt="17740702071721631643988491817250" src="https://github.com/user-attachments/assets/75a9cea3-2698-46ff-94d7-a1bae9175333" />

The sender's kernel space buffers the data from the user space to protect the controller from transmitting the data actively being modified by the user (transmitting mid-write could result in the transmission of garbled data), whereas the receiver's kernel space buffers the data from the controller to ensure it's not lost in case the receiver's user process is not ready to receive the data (its memory is paged out, etc).

## Why do processes send data to the printer through a spooler rather than directly?

Because a rogue process could end up locking the printer indefinitely, locking all other processes out of having access to it.

> Although it would be technically easy to let any user process open the character special file for the printer, suppose a process opened it and then did nothing for hours. No other process could print anything. Instead what is done is to create a special process, called a daemon, and a special directory, called a spooling directory. To print a file, a process first generates the entire file to be printed and puts it in the spooling directory. It is up to the daemon, which is the only process having permission to use the printer’s special file, to print the files in the directory. By protecting the special file against direct use by users, the problem of having someone keeping it open unnecessarily long is eliminated.

The spooler process is written specifically to send a file to the printer as soon as it's added to the spooling directory (or as soon as the printer is done printing the previous file if the directory is not empty, in the FIFO order).

## How to have an elevator in your building running efficiently? 

Use the shortest seek first (SSF) algorithm: when multiple floors are waiting for the elevator, always go to the closest one.

<img width="864" height="283" alt="17740702387365230334225926133921" src="https://github.com/user-attachments/assets/4e1326f0-692c-49fb-af49-a0673773e11e" />

However, efficiency is not the only goal for a building elevator. It must also be fair. The rotational disk suffers from the same problem: with SSF, just as the disk arm will stay in the middle most of the time, starving out the requests at the edges, so will the elevator spend most of its time on the middle floors, rarely reaching the ground or the top floor.

> With a heavily loaded disk, the arm will tend to stay in the middle of the disk most of the time, so requests at either extreme will have to wait until a statistical fluctuation in the load causes there to be no requests near the middle. Requests far from the middle may get poor service. The goals of minimal response time and fairness are in conflict here.

The algorithm that optimizes for fairness, first-come first-served, is inefficient, so a new algorithm is needed. One proposed algorithm relies on remembering the direction bit.

> When a request finishes, the disk or elevator driver checks the bit. If it is UP, the arm or cabin is moved to the next highest pending request. If no requests are pending at higher positions, the direction bit is reversed. When the bit is set to DOWN, the move is to the next lowest requested position, if any. If no request is pending, it just stops and waits. In big office towers, when there are no requests pending, the software might send the cabin to the ground floor, since it is more likely to be need there shortly than on, say, the 19th floor. Disk software does not usually try to speculatively preposition the head anywhere.

The elevator algorithm successfully balances efficiency and fairness for rotational disks and building elevators alike. 

<img width="864" height="309" alt="17740702603193835068103346981714" src="https://github.com/user-attachments/assets/2858e542-400b-4b83-ad33-e8df82c97010" />

## What is a device driver? 

It's a layer of software below device-independent I/O library procedures provided by the OS. Once a driver is installed, its procedure calls are registered in the kernel's function pointer table. When a program calls a device-independent I/O library procedure, the OS finds the driver's procedures for the target hardware service in the function pointer table and calls the one mapped to the I/O library procedure.

> Operating systems, starting with MS-DOS, went over to a model in which drivers were dynamically loaded into the system during execution.

Dynamic linking exists to separate the driver from the rest of the operating system, which reduces the need to reboot the system on hardware change (e.g., after plugging it in).

> An OS can facilitate installation of a new device without any need for recompiling the OS.

Driver's procedures in the kernel's function pointer table include device-specific versions of read and write, as well as procedures for initialization and power management.

> A device driver has several functions. The most obvious one is to accept abstract read and write requests from the device-independent software above it and see that they are carried out. But there are also a few other functions it must perform. For example, the driver must initialize the device, if needed. It may also need to manage its power requirements and log events.

In an attempt to conserve the battery, the OS periodically calls drivers' power management procedures requesting them to cut their power levels.

## Can the controller of a magnetic disk act as a standalone computer?

If hacked, sure. Hard disks have processors and caches. A cluster computer made entirely of discarded hard disks is possible.

> A highly convincing demonstration of how advanced disk controllers have become was given by the Dutch hacker Jeroen Domburg, who hacked a modern disk controller to make it run custom code. It turns out the disk controller is equipped with a fairly powerful multicore ARM processor and has easily enough resources to run Linux. If the bad guys hack your hard drive in this way, they will be able to see and modify all data you transfer to and from the disk. Even reinstalling the operating from scratch will not remove the infection, as the disk controller itself is malicious and serves as a permanent backdoor. Alternatively, you can collect a stack of broken hard drives from your local recycling center and build your own cluster computer for free.

## What is the carbon footprint of a desktop computer?

Together, all desktop computers in the world need about 20 power plants to run.

> A desktop PC often has a 200-watt power supply (which is typically 85% efficient, that is, loses 15% of the incoming energy to heat). If 100 million of these machines are turned on at once worldwide, together they use 20,000 megawatts of electricity. This is the total output of 20 average-sized nuclear power plants. If power requirements could be cut in half, we could get rid of 10 nuclear power plants. From an environmental point of view, getting rid of 10 nuclear power plants (or an equivalent number of fossil-fuel plants) is a big win for the planet.

## If the CPU clock is always running while the computer is on and active, why is it that the battery drain on a battery-powered computer depends on the workload and isn't uniform? 

Because the CPU turns off portions of its circuitry when unneeded (the utilization is low) and also the clock itself is made to run slower.

> In P0, a specific processor may operate at its maximum performance of 3.6GHz and 1.4V, in P1 at 3.4GHz and 1.35V and so on, until we get to a minimum level of, say, 2.8GHz and 1.2V. These power states may be controlled by software, but often the CPU itself tries to pick the right P-state for the current situation. For instance, when it notices that the utilization decreases, it may try to reduce the performance and hence the power consumption of the CPU by automatically switching to higher P-states.

The slower clock reduces the necessary voltage supply to the CPU circuitry, and turning off parts of this circuitry reduces it even more. Supply voltage is the biggest contributor to power consumption.

## Why do messages sometimes take a long time to reach the smartphone?

Because they turn off their radios to conserve power. The messages sit in the queue on the base stations until the device turns the radio back on.

> Have the mobile computer send a message to the base station when it is about to turn off the radio. From that time on, the base station buffers incoming messages on its disk. The mobile computer may indicate explicitly how long it is planning to sleep, or simply inform the base station when it switches on the radio again. At that point any accumulated messages can be sent to it. Outgoing messages that are generated while the radio is off are buffered on the mobile computer. If the buffer threatens to fill up, the radio is turned on and the queue transmitted to the base station.

This way, we make the most of the device that's already always on (the base station) and reduce the load on the device that needs to conserve power (the smartphone).

> Mobile devices (e.g., smartphones) communicate with fixed base stations that have large memories and disks and no power constraints.

WiFi works the same way. 

> In 802.11, a mobile computer can notify the access point that it is going to sleep but it will wake up before the base station sends the next beacon frame. The access point sends out these frames periodically. At that point the access point can tell the mobile computer that it has data pending. If there is no such data, the mobile computer can sleep again until the next beacon frame.

Alternating between remote and local processing in this way is a viable power management technique when performance degradation alone isn't enough.

> We may save power by pushing a computationally expensive operation to the cloud rather than executing it on, say, a smartphone. Whether this is a good idea is a tradeoff between the cost of executing things locally versus the energy cost of operating the radio. Of course, other considerations such as performance (will the delay go up?), security (do we trust the cloud with our computation?), and reliability (what if we do not have connectivity?) also play a role.

## How could a cable purchased from a disreputable source become a security vulnerability when plugged into a computer?

A Thunderbolt/FireWire cable could read data from the shared memory bus enabled by direct memory access and potentially transmit it to the attacker.

> I/O improvements in hardware may offer new opportunities for attackers. A good example is DMA which is good for efficiency, but may allow malicious devices (such as a display cable that has been tampered with) to access memory to which they should not have access.

A USB cable has no DMA access but could instead masquerade as a keyboard and covertly send a set of keystrokes that could also exfiltrate potentially sensitive data from the machine. 
