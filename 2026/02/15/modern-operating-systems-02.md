# 2. Processes and Threads

This chapter of [Modern Operating Systems](../../../2026/01/06/modern-operating-systems.md) answered eight questions about how operating systems and user programs interact with the CPU.

## What is the difference between a process and a thread?

The difference lies in purpose: one is for resource management and the other is to control the flow of command execution.

> Processes are used to group resources together; threads are the entities scheduled for execution on the CPU.

A process is a container.

> It is a convenient way to group together related resources. A process has an address space that contains program text and data, as well as other resources. These resources may include open files, child processes, pending alarms, signal handlers, accounting information, and more.

A process contains allocations of system resources. How does one allocate CPU resources? With threads of execution. So, a process contains not only address spaces, open files, and bookkeeping information. It also contains threads of execution.

> The thread has a program counter associated with it that keeps track of which instruction to execute next. It has registers, which hold its current working variables. It also has a stack, which contains the thread’s execution history, one frame for each procedure called but not yet returned from.

When a process has multiple threads, they share the resources allocated to the process. As a consequence, they can read from and write to each other's memory.

## Can a process yield CPU to another process like threads do with pthread_yield?

Not explicitly. 

> There is no such call for processes because the assumption there is that processes are fiercely competitive and each wants all the CPU time it can get (although a very public-spirited process could call sleep to yield the CPU briefly).

One commonly sees calls to sleep in processes looping through API calls (to respect the API's rate limit) or those polling other processes for a certain status (e.g., checking every minute to see if some process has finished before shutting down the system). In both of those cases, sleep prevents one process from hogging system resources unnecessarily, which is what pthread_yield does for threads, albeit without a timer. One could argue that processes don't need to yield to other processes because the scheduler already takes care of the yielding. Where user-level threads packages call pthread_yield (e.g., mutex_lock), the process counterpart of such a function simply sits busy-waiting until the scheduler takes the CPU resource away from it.

```assembly
mutex_lock:
    TSL REGISTER,MUTEX        | copy mutex to register and set mutex to 1
    CMP REGISTER,#0           | was mutex zero?
    JZE ok                    | if it was zero, mutex was unlocked, so return
    CALL thread_yield         | mutex is busy; schedule another thread
    JMP mutex_lock            | try again
ok:
    RET                       | return to caller; critical region entered

mutex_unlock:
    MOVE MUTEX,#0             | store a 0 in mutex
    RET                       | return to caller


enter_region:
    TSL REGISTER,LOCK         | copy lock to register and set lock to 1
    CMP REGISTER,#0           | was lock zero?
    JNE enter_region          | if it was not zero, lock was set, so loop
    RET                       | return to caller; critical region entered

leave_region:
    MOVE LOCK,#0              | store a 0 in lock
    RET                       | return to caller
```

## What is a finite state machine?

A program that maintains an internal state and reacts to events that modify it.

> Each computation has a saved state, and there exists some set of events that can occur to change the state.

Whereas multithreading improves performance by enabling certain computations to be performed in parallel, a finite state machine may improve performance even further by eliminating the need for blocking interrupts.

> It is very popular in high-throughput servers where even threads are considered too expensive and instead an event-driven programming paradigm is used. By implementing the server as a finite state machine that responds to events (e.g., the availability of data on a socket) and interacting with the operating system using non-blocking or asynchronous system calls, the implementation can be very efficient. Every event leads to a burst of activity, but it never blocks.

A server written as a finite state machine may repeatedly ask which devices/files are ready for I/O (devices that will respond to system calls without blocking). Once a set of such devices is selected, the server executes the necessary I/O system calls on them (without them blocking the thread of execution, as promised), and by the time these calls are done, there will likely be another set of devices/files ready for nonblocking I/O.

> When a request comes in, the one and only thread examines it. If it can be satisfied from the cache, fine, but if not, a nonblocking disk operation is started. The server records the state of the current request in a table and then goes and gets the next event. The next event may either be a request for new work or a reply from the disk about a previous operation. If it is new work, that work is started. If it is a reply from the disk, the relevant information is fetched from the table and the reply processed. With nonblocking disk I/O, a reply probably will have to take the form of a signal or interrupt.

Reaping the benefits of event-driven execution comes with a cost in terms of code complexity: the program must explicitly keep track of the state of every file, whether it was recently marked as ready for nonblocking I/O, how much data has already been read from it/written to it the last time it became ready so the program can continue the data stream from the right place, etc.

> The state of the computation must be explicitly saved and restored in the table every time the server switches from working on one request to another.

Switching from a finite-state machine to multithreading can simplify the task of programming. For example, MINIX 3's kernel consists of finite state machines, but anything more complex (e.g., the Linux kernel) usually prompts programmers to enlist the help of the threads library.

> The Linux kernel on modern Intel CPUs is a multithreaded operating system kernel. In contrast, MINIX 3 consists of many servers implemented following the model of finite state machine and events.

## Why is strict alternation insufficient for solving race conditions? 

Because a satisfactory solution to the race-condition problem has a progress requirement, and strict alternation violates it.

> No process running outside its critical region may block any process.

Suppose process 0 notices that the value of the shared variable turn has flipped to 0, so it enters its critical region after which it flips the value back to 1.

```c
while (TRUE) {
    while (turn != 0) { }   /* loop */
    critical_region();
    turn = 1;
    noncritical_region();
}
```

Now process 1 notices that the value of turn has flipped to 1, so it can run its critical region and flip it back to 0.

```c
while (TRUE) {
    while (turn != 1) { }   /* loop */
    critical_region();
    turn = 0;
    noncritical_region();
}
```

What if process 1 needs to run its critical region again before process 0 runs again? It has to wait for process 0 to run again. What if process 0 never needs to run again? This is where the progress stalls. Without the guarantee that work is evenly split across two processes that will strictly alternate, strict alternation does not solve race conditions effectively. [Peterson's solution](https://chatgpt.com/share/6975b289-e568-8011-a98e-2e850f7496c1) fixes this by introducing another shared variable, _interested_.

```c
while (TRUE) {
    interested[0] = TRUE;
    turn = 1;
    while (interested[1] && turn == 1) { }
    critical_region();
    interested[0] = FALSE;
    noncritical_region();
}
```

This way, if process 0 isn't running, then process 1 can detect that and safely enter its critical region out of turn. 

```c
while (TRUE) {
    interested[1] = TRUE;
    turn = 0;
    while (interested[0] && turn == 0) { }
    critical_region();
    interested[1] = FALSE;
    noncritical_region();
}
```

## How do systems with multiple CPUs resolve race conditions?

By locking the memory bus for all CPUs except for the one locking it. Disabling interrupts is insufficient in this context.

> Disabling interrupts then performing a read on a memory word followed by a write does not prevent a second processor on the bus from accessing the word between the read and the write. In fact, disabling interrupts on processor 1 has no effect at all on processor 2. The only way to keep processor 2 out of the memory until processor 1 is finished is to lock the bus.

## Why should busy waiting be avoided? 

Not just for performance reasons. There's also the priority inversion problem. 

> Consider a computer with two processes, H, with high priority, and L, with low priority. The scheduling rules are such that H is run whenever it is in ready state. At a certain moment, with L in its critical region, H becomes ready to run (e.g., an I/O operation completes). H now begins busy waiting, but since L is never scheduled while H is running, L never gets the chance to leave its critical region, so H loops forever.

A deadlock arises when a low-priority process doesn't allow the high-priority process to enter its critical region and the high-priority process is given priority over the low-priority process. 

## What do semaphores do? 

They guard against certain exceptional conditions that would make a program crash. 

> Needed to guarantee that certain event sequences do or do not occur.

For example, semaphores solve the producer-consumer problem by blocking consumers from reading from below an empty buffer and producers from writing into a buffer overflow.

> They ensure that the producer stops running when the buffer is full, and that the consumer stops running when it is empty.

A binary semaphore can ensure only one process at a time is in its critical region.

> The mutex semaphore is used for mutual exclusion. It is designed to guarantee that only one process at a time will be reading or writing the buffer and the associated variables.

## What is a futex?

A faster mutex.

> A futex is a feature of Linux that implements basic locking, much like a mutex, but avoids dropping into the kernel unless it really has to.

What makes a futex faster than mutex is that it avoids busy waiting by trapping to the kernel when trapping to the kernel is less expensive than busy waiting.

> Spin locks, and mutexes implemented by busy waiting in general, are fast if the wait is short, but waste CPU cycles if not. If there is much contention, it is therefore more efficient to block the process and let the kernel unblock it only when the lock is free. Unfortunately, this has the inverse problem: it works well under heavy contention, but continuously switching to the kernel is expensive if there is very little contention to begin with. To make matters worse, it may not be easy to predict the amount of lock contention.

A futex relies on a heuristic: since there's no contention most of the time, then relying on user-level mutex should grant the lock immediately. But if it fails and we have to wait on the lock, that means there is contention. A futex assumes that there's no point in waiting and so it traps to the kernel to join a wait queue on the contended resource. The kernel will wake the process/thread up when the contention is resolved.

> The kernel service provides a wait queue that allows multiple processes to wait on a lock. They will not run unless the kernel explicitly unblocks them. For a process to be put on the wait queue requires an expensive system call. If possible, it should be avoided. In the absence of any contention, therefore, the futex works entirely in user space. Specifically, the processes or threads share a common lock variable, a fancy name for an integer in shared memory that serves as the lock. Suppose we have a multithreaded program and the lock is initially minus 1, which we assume to mean that the lock is free. A thread may grab the lock by performing an atomic decrement and test. Next, the thread inspects the result to see whether or not the lock was free. If it was not in the locked state, all is well and our thread has successfully grabbed the lock.
However, if the lock is held by another thread, our thread has to wait. In that case, the futex library does not spin, but uses a system call to put the thread on the wait queue in the kernel. Hopefully, the cost of the switch to the kernel is now justified, because the thread was blocked anyway. When a thread is done with the lock, it releases the lock with an atomic increment and test and checks the result to see if any processes are still blocked on the kernel wait queue. If so, it will let the kernel know that it may wake up, unblock, one or more of these processes. In other words, if there is no contention, the kernel is not involved at all.
