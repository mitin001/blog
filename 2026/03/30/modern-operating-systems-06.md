# 6. Deadlocks

This chapter of [Modern Operating Systems](../../../2026/01/06/modern-operating-systems.md) answered five questions about situations where two processes are stuck waiting for each other.

## When should an operating system look for deadlocks?

When the CPU is idle enough to be able to handle the overhead of constructing resource graphs and detecting cycles in them. Opting to detect deadlocks as early as possible would, on the other hand, waste too many valuable CPU cycles.

> One possibility is to check every time a resource request is made. This is certain to detect them as early as possible, but it is potentially expensive in terms of CPU time. An alternative strategy is to check every k minutes, or perhaps only when the CPU utilization has dropped below some threshold. The reason for considering the CPU utilization is that if enough processes are deadlocked, there will be few runnable processes, and the CPU will often be idle.

Why waste time looking for a problem when, most of the time, you wouldn't find one? On the other hand, if you have many stuck processes in the queue, then we can be reasonably sure that a problem has indeed occurred, and the time has come to solve it.

## How to avoid deadlocks? 

Have the operating systems look at resource allocations across processes every time a process requests a resource. If granting the request leads to an unsafe state, suspend the process until satisfying the request no longer leads to an unsafe state. For example, when process A crosses time point I1, it requests and is granted the printer; when process B requests a plotter at time point I5, it should only be granted this resource after process A has passed time point I4, at which point it has released both of the resources. If process B is granted access to the plotter at time t, before A releases its resources, it will enter an unsafe state where advancing either process brings it toward the impossible situation of mutual exclusion (where both processes would be using the same resource).

![17748532421183375633640541988780](https://github.com/user-attachments/assets/ab59a8fa-c9ec-460f-9edf-06a9796b423f)

As another example, if there are two free instances of a resource, and only one of the processes would complete (and thus release its resources) if these are granted to it (process C), then the only way to avoid an unsafe state is to grant the resources to this process. Giving them to another process would lead to a situation where we have zero resources left and no process that can finish (thereby releasing all of its resources).

<img width="300" alt="17748532806173693259202628552436" src="https://github.com/user-attachments/assets/17108d93-00ba-48fd-8a53-40478eabbdcf" />

Of course, a process could release some of its resources well before it exits, but we can't count on that if we want to guarantee deadlock avoidance. On the other hand, some situations guarantee the impossibility of deadlocks because there is no possible resource allocation that would lead to an unsafe state.

> A system has two processes and three identical resources. Each process needs a maximum of two resources.

In general, if there are p processes each requiring at most m resources to complete, then as long as there are more than p(m-1) resources available, deadlocks are impossible. In the worst case, each process will be in an incomplete state holding m-1 resources, but since there will still be at least one more resource available than this total, the allocation will lead to one of the processes completing, which will ensure there are, once again, enough resources for the others to complete. However, note that situations like this, and this algorithm in general (Dijkstra's banker's algorithm), rely on assumptions that, in many situations, are unrealistic, which means deadlock avoidance isn't always possible.

> Few authors have had the audacity to point out that although in theory the algorithm is wonderful, in practice it is essentially useless because processes rarely know in advance what their maximum resource needs will be. In addition, the number of processes is not fixed, but dynamically varying as new users log in and out. Furthermore, resources that were thought to be available can suddenly vanish (tape drives can break). Thus, in practice, few, if any, existing systems use the banker’s algorithm for avoiding deadlocks. Some systems, however, use heuristics similar to those of the banker’s algorithm to prevent deadlock. For instance, networks may throttle traffic when buffer utilization reaches higher than, say, 70%—estimating that the remaining 30% will be sufficient for current users to complete their service and return their resources.

If deadlock avoidance is impossible, the next best thing is deadlock prevention: resource allocation to processes is to be minimized. 

> Avoid assigning a resource unless absolutely necessary, and try to make sure that as few processes as possible may actually claim the resource.

Since four conditions are necessary for creating a deadlock, a deadlock prevention algorithm works by simply restricting the system from allowing one or more of such conditions. 

<img width="400" alt="17748533003663503272064275332233" src="https://github.com/user-attachments/assets/50c247ad-bd45-45e0-ad0c-8d575c8a85fe" />

For example, if a process holding resource A is not allowed to wait for another resource (the hold-and-wait condition), then it will definitely not be waiting for a resource, say resource B, that could only be freed by a process waiting for resource A.

> If we can prevent processes that hold resources from waiting for more resources, we can eliminate deadlocks. One way to achieve this goal is to require all processes to request all their resources before starting execution. If ev erything is available, the process will be allocated whatever it needs and can run to completion. If one or more resources are busy, nothing will be allocated and the process will just wait.

New York City eliminates the hold-and-wait condition by not allowing a car to hold up an intersection unless it can immediately leave it (the street it needs has space to accommodate it) and punishing violators with fines.

> City streets are vulnerable to a circular blocking condition called gridlock, in which intersections are blocked by cars that then block cars behind them that then block the cars that are trying to enter the previous intersection, etc. All intersections around a city block are filled with vehicles that block the oncoming traffic in a circular manner. Gridlock is a resource deadlock and a problem in competition synchronization. New York City’s prevention algorithm, called ‘‘don’t block the box,’’ prohibits cars from entering an intersection unless the space following the intersection is also available.

Gridlocks are not just a vulnerability of a city. It can occur in any graph with a cycle. This is why routers don't accept an incoming packet if doing so would fill up its buffer.

<img width="500" alt="17748533214048749201108838368639" src="https://github.com/user-attachments/assets/b7e90688-7a66-4236-b245-6281c5bc8983" />

In the context of operating systems, targeting the hold-and-wait condition could mean disallowing partial allocations of resources: a process either gets all the resources it will ever need upfront or it must give all of its allocations up if it ever finds itself in a situation where it needs to request more. The former is a better idea than the latter. Releasing resources half-way means potentially abandoning the progress made with them up to that point. This could make for a thrashing process.

> It may get the new resource but lose some of the existing ones to competing processes.

Ordering resources numerically is another idea for avoiding curcular waits. This is how deadlocks are commonly avoided in electronic funds transfer systems.

> Each process reads an input line specifying an amount of money, the account to be credited, and the account to be debited. Then it locks both accounts and transfers the money, releasing the locks when done. With many processes running in parallel, there is a very real danger that a process having locked account x will be unable to lock y because y has been locked by a process now waiting for x.

If every process always locks accounts in the same order (e.g., low-numbered account first and high-numbered account second), then there is no circular wait, and deadlocks are avoided.

## How to convert a non-preemptible resource into a preemptible one?

Virtualize it, if possible. For example, instead of writing directly to a printer, write to a file (_virtual printer_) and have a dedicated non-preemptible process feed the data from the virtual file to the physical printer. That way, you're not starting another non-preemptible process. The fewer non-preemptible processes, the less likely the system is to deadlock.

> Spooling printer output to the SSD or disk and allowing only the printer daemon access to the real printer eliminates deadlocks involving the printer, although it creates a potential for deadlock over disk space. With large SSDs/disks though, running out of storage space is unlikely.

## Can two processes deadlock if they're not sharing resources?

Yes, processes don't just wait for resources. They could also be waiting for messages. If process A sends a message to process B and it gets dropped, then both processes will deadlock: A will be stuck waiting for an acknowledgement from B, and B will be stuck waiting for the message from A.

> We have a set of (two) processes, each blocked waiting for an event only the other one can cause. This situation is called a communication deadlock to contrast it with the more common resource deadlock. Communication deadlock is an anomaly of cooperation synchronization.

Communication deadlocks (and sometimes even resource deadlocks) are resolved with timeouts. If a process doesn't receive a message in a timely manner, it moves on.

> In most network communication systems, whenever a message is sent to which a reply is expected, a timer is started. If the timer goes off before the reply arrives, the sender of the message assumes that the message has been lost and sends it again (and again and again if needed). In this way, the deadlock is broken. Phrased differently, the timeout serves as a heuristic to detect deadlocks and enables recovery. This heuristic is applicable to resource deadlocks also and is relied upon by users with buggy device drivers that can deadlock and freeze the system.

Communication deadlocks are to blame for the TCP zero-window problem.

> In order to control traffic, a network router, A periodically sends a message to its neighbor, B, telling it to increase or decrease the number of packets that it can handle. At some point in time, Router A is flooded with traffic and sends B a message telling it to cease sending traffic. It does this by specifying that the number of bytes B may send (A’s window size) is 0. As traffic surges decrease, A sends a new message, telling B to restart transmission. It does this by increasing the window size from 0 to a positive number. That message is lost. As described, neither side will ever transmit.

Just as timeouts resolve communication deadlocks, a persist timer solves the TCP zero-window problem.

## What is a livelock?

It's when two people bump into each other and both try to yield to the other, and no one is moving as a result.

> The situation of two people trying to pass each other on the street when both of them politely step aside, and yet no progress is possible, because they keep stepping the same way at the same time.

Just like a deadlock, a livelock of a way of reaching an impasse. And just like a deadlock, a livelock can occur in an operating system.

> A process tries to be polite by giving up the locks it already acquired whenever it notices that it cannot obtain the next lock it needs. Then it waits a millisecond, say, and tries again.

A livelock arises out of a deadlock prevention strategy: a process only allows itself to acquire a lock if it's not in contention.

> Suppose that a UNIX system has 100 process slots. Ten programs are running, each of which needs to create 12 children. After each process has created 9 processes, the 10 original processes and the 90 new processes have exhausted the table. Each of the 10 original processes now sits in an endless loop forking and failing—a livelock. The probability of this happening is minuscule, but it could happen.

Processes resolve a livelock by randomizing their wait times: if every process waited the same multiple of the clock cycle to acquire or release locks, they could be stuck requesting and releasing locks in lockstep. If the processes wait random times, they'll eventually find a situation where one can proceed because their other one's wait time was long enough to allow it. Two people resolve a livelock by having one of them lose patience first, which will push them into stopping being so polite and finally taking the right of way the other one is hopefully still yielding to them. Symmetries create deadlocks and livelocks. Breaking the symmetry breaks the deadlock/livelock.
