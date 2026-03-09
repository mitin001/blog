# 4. File Systems

This chapter of [Modern Operating Systems](../../../2026/01/06/modern-operating-systems.md) answered ten questions about a computer's persistent storage.

## What's the difference between a hard link and a symbolic link?

A hard link is created with the _link_ system call.

> Increments the counter in the file's i-node (to keep track of the number of directory entries containing the file).

In a way, every file is a hard link. Once you unlink a file with only one entry remaining in its i-node, the file is deleted. Meanwhile, a symbolic link (shortcut, alias) is just a text file containing the location of another file. 

> Instead of having two names point to the same internal data structure representing a file, a name can be created that points to a tiny file naming another file. When the first file is used, for example, opened, the file system follows the path and finds the name at the end. Then it starts the lookup process all over using the new name. Symbolic links have the advantage that they can cross disk boundaries and even name files on remote computers.

## What happens when a computer starts up?

Depends on the partition scheme of the hard drive connected to it. If the BIOS (firmware) reads sector 0 of the drive and determines that its partition scheme is MBR, it looks up the start address of the active partition in it and uses it to find the boot block, which it loads into main memory.

> Sector 0 of the disk is called the MBR (Master Boot Record) and is used to boot the computer. The end of the MBR contains the partition table. This table gives the starting and ending addresses of each partition. One of the partitions in the table is marked as active. When the computer is booted, the BIOS reads in and executes the MBR. The first thing the MBR program does is locate the active partition, read in its first block, which is called the boot block, and execute it. The program in the boot block loads the operating system contained in that partition. For uniformity, every partition starts with a boot block, even if it does not contain a bootable operating system. Besides, it might contain one in the future.

The boot block contains the OS bootloader, which initializes the kernel, which will later rely on the information from the superblock to initialize the OS file system.

<img width="500" alt="Screenshot_20260308-235204" src="https://github.com/user-attachments/assets/ab8e4e84-edcb-44b9-b981-87b514f5e11b" />

If sector 0 is not MBR, then it assumes GPT and proceeds to sector 1. Of course, this only works on the firmware that supports GPT, which is UEFI (Unified Extensible Firmware Interface).

<img width="700" alt="Screenshot_20260308-235538" src="https://github.com/user-attachments/assets/6badb7de-87af-4cca-993d-df3bd383ab63" />

UEFI can mount an EFI boot partition from a GPT drive and boot an OS from that.

> Rather than a single magic boot sector, the boot process can now use a proper file system containing programs, configuration files, and anything else that may be useful during boot. Moreover, UEFI expects the firmware to be able to execute programs in a specific format, called PE (Portable Executable). In other words, the firmware under UEFI looks like a small operating system itself with an understanding of disk partitions, file systems, executables, etc.

## What does it mean for an operation to be idempotent?

Such operations are repeatable. A journaling file system is an example of a system composed entirely of idempotent actions.

> They can be repeated as often as needed without harm. Operations such as ‘‘Update the bitmap to mark i-node k or block n as free’’ can be repeated until the cows come home with no danger. Similarly, searching a directory and removing any entry called foobar is also idempotent. On the other hand, adding the newly freed blocks from i-node K to the end of the free list is not idempotent since they may already be there. The more-expensive operation ‘‘Search the list of free blocks and add block n to it if it is not already present’’ is idempotent.

Idempotent functions are easier to test because we can run them as many times as needed for adequate testing without having to undo their effects after each run.

## If you replace one character in a file on an SSD, will it still occupy the same block after saving? 

No, the contents of the whole flash page around the modified character will be copied into a new flash page.

> Modifying data on an SSD simply makes the old flash page invalid and then rewrites the new content in another block.

This is because we cannot overwrite flash memory without erasing it first and the erase operation accepts blocks of pages, not individual pages.

> The SSD cannot really overwrite a flash page that was written earlier. It first has to erase the entire flash block again (not just the page).

An SSD spreads out its writes in such a way that ideally we will only come back to the first block after all the other blocks have been written to. There is a set number of times a block can be overwritten before it can no longer be used physically.

> Typical flash memory cells have a maximum endurance of a few thousand to a few hundred thousand P/E cycles before they kick the bucket. In other words, it is important to spread the wear across the flash memory cells as much as possible.

Even a single byte update to a file leads to a cascade of metadata updates, especially if the file's i-node is large enough to require an indirect block. The recursive update problem (wandering tree problem) makes ext4 (and NTFS) a poor fit for SSDs (if the historical design assumptions still hold).

> Besides writing the updated flash page to a new block, the file system also needs to update the indirect block, since the logical (disk) address of the file data has changed. The update means that the flash page corresponding to the indirect block must be moved to another flash block. In addition, because the logical address of the indirect block has now changed, the file system should also update the i-node itself—leading to a new write to a new flash block. Finally, since the i-node is now in a new logical disk block, the file system must also update the i-node map, leading to another write on the SSD. In other words, a single file update leads to a cascade of writes of the corresponding metadata. In real log-structured file systems, there may be more than one level of indirection (with double or even triple indirect blocks), so there will be even more writes.

However, optimizations subsequently made to ext4, NTFS, and FTL (SSD firmware) have nearly closed the performance gap that existed when SSDs first came on the market optimized for magnetic disks.

## What is the TRIM command?

A way for the file system to provide information to an SSD's flash translation layer (FTL) that it never needed to provide to older disk firmware. The information in question is which block is free (which block contains the data that won't ever need to be read). This way, the FTL can include the block in garbage collection to help with wear leveling.

> The file system may decide to delete a file and mark the logical block addresses as free, but how is the SSD to know which of its flash pages have been deleted and can therefore be safely garbage collected? The answer is: it does not and needs to be told explicitly by the file system. For this, the file system may use the TRIM command which tells the SSD that certain flash pages are now free. Note that an SSD without the TRIM command still works (and indeed some operating systems have worked without TRIM for years), but less efficiently. In this case, the SSD would only discover that the flash pages are invalid when the file system tries to overwrite them. We say that the TRIM command helps bridge the semantic gap between the FTL and the file system—the FTL does not have sufficient visibility to do its job efficiently without some help. It is a major difference between file systems for hard disks and file systems for SSD.

In other words, TRIM is an optimization command. 

## What happens when a disk block goes bad?

During installation or disk formatting, the operating system creates a file that keeps track of bad blocks. Whenever a bad block is encountered, it is assigned to this file, thereby taking it out of the pool of free blocks.

> Sometimes blocks go bad after formatting, in which case the operating system will eventually detect them. Usually, it solves the problem by creating a ‘‘file’’ consisting of all the bad blocks—just to make sure they nev er appear in the free-block pool and are never assigned.

Some bad blocks are never discovered by the operating system because they are handled by the disk firmware (e.g., bad blocks created by manufacturing defects). In this case, the firmware simply remaps the bad block to the spare block.

> Sometimes when a low-level format is done, the bad blocks are detected, marked as bad, and replaced by spare blocks reserved at the end of each track for just such emergencies. In many cases, the disk controller handles bad-block replacement transparently without the operating system even knowing about it.

## When performing a backup of a file system, should any files be ignored?

Yes, and not just for the sake of keeping the backup free of unneeded files (like temporary, cache, paging, and hibernation files), but also to keep the backup from stumbling into bad blocks by opening the file meant to shield the file system from them.

> If all bad blocks are remapped by the disk controller and hidden from the oper- ating system as just described, physical dumping works fine. On the other hand, if they are visible to the operating system and maintained in one or more bad-block files or bitmaps, it is absolutely essential that the physical dumping program get access to this information and avoid dumping them to prevent endless disk read errors while trying to back up the bad-block file. Windows systems have paging and hibernation files that are not needed in the ev ent of a restore and should not be backed up in the first place.

Also, not all files in a file system are mapped to disk blocks, and those that are not should likewise be ignored during backups, not just for performance reasons but to avoid errors and timeouts.

> In UNIX, all the special files (I/O devices) are kept in a directory /dev. Not only is backing up this directory not necessary, it is downright dangerous because the backup program would hang forever if it tried to read each of these to completion.

## What does fsck do if it discovers that the same disk block is present in two files? 

fsck must copy the contents of the block discovered to be in use twice (say block 5) to another block and assign the copy destination block to one of the files referencing it. If it doesn't do that, the files will be encroaching on each other with every action they take that involves the "shared" block.

> If either of these files is removed, block 5 will be put on the free list, leading to a situation in which the same block is both in use and free at the same time. If both files are removed, the block will be put onto the free list twice. The appropriate action for the file-system checker to take is to allocate a free block, copy the contents of block 5 into it, and insert the copy into one of the files. In this way, the information content of the files is unchanged (although almost assuredly one is garbled), but the file-system structure is at least made consistent. The error should be reported, to allow the user to inspect the damage.

## Why should you eject the drive before removing it from the computer?

Because even if you've saved changes to all of the drive's open files, they may not yet have made it to the drive. Saving a file saves your changes to the file system cache in main memory. Until the cache is flushed, the changes haven't been committed to the disk. The eject operation ensures the cache flush happens before the drive is marked as safe to remove. The cache flush happens through the invocation of the sync system call. 

> Forces all the modified blocks out onto the disk immediately. When the system is started up, a program, usually called _update_, is started up in the background to sit in an endless loop issuing _sync_ calls, sleeping for 30 sec between calls. As a result, no more than 30 seconds of work is lost due to a crash.

By bypassing the eject operation, you risk not only losing the recent changes to the files but also corrupting the drive's file system.

> If a critical block, such as an i-node block, is read into the cache and modified, but not rewritten to the disk, a crash will leave the file system in an inconsistent state.

Early versions of Windows were less damaging to unejected disks because its disk caches were write-through caches.

> What it did was to write every modified block to disk as soon as it was written to the cache.

Windows was originally developed for removable disks (floppies), but its approach for disk cache had poor performance, and so it was abandoned, even as the need to support removable disks never went away.

> UNIX was developed in an environment in which all disks were hard disks and not removable, whereas the first Windows file system was inherited from MS-DOS, which started out in the floppy-disk world. As hard disks became the norm, the UNIX approach, with its better efficiency (but worse reliability), became the norm, and it is also used now on Windows for hard disks.

## How do compression algorithms work?

Sometimes by simple deduplication. They look for multiple occurrences of the same data and replace all subsequent occurrences with pointers to the first one. If the pointers take less space than the duplicated data, then this compression algorithm yields some space savings.

> The compression algorithms commonly look for repeating sequences of data which they then encode efficiently. For instance, when writing file data they may discover that the 133 bytes at offset 1737 in the file are the same as the 133 bytes at offset 1500, so instead of writing the same bytes again, they insert a marker (237,133)—indicating that these 133 bytes can be found at a distance of 237 before the current offset.
