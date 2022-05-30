# TBus

<!-- TOC -->

- [TBus](#tbus)
    - [Overview](#overview)
    - [Appendix: Shared Memory](#appendix-shared-memory)

<!-- /TOC -->

## Overview

TBus 为 Game Server 提供两套 API 进行使用:

- tbus_api，这种方式需要使用 tconnapi_decode 去掉 tfreamehead。
- tconnapi，推荐使用这种方式。

## Appendix: Shared Memory

Tconnd 接收到数据会，通过 TBus 的共享内存机制将数据转发给 Game Svr，这里对共享内存做一点阐述。

早期 Linux 共享内存是用 mmap 函数来进行地址做到的共享内存，但是现在一般不会用 mmap 而是用另外一种：XSI IPS。

XSI IPC 是进程间通信结构，它不仅包含了共享内存，也包含了消息队列、信号量。

IPC 的标识：

- IPC 内部标识：
  - 对于内核中的 IPC 结构（是的，所有 IPC 元数据都是存放在内核内存中的），都有一个非负整数 identifier 进行标识和引用。
- IPC 外部标识：
  - identifier 是 IPC 的内部名称
  - 为了让多个进程进行合作，需要让它们通过某种机制获得这个 identifier，因此提供了一个外部名称，即 key。
  - 无论何时创建 IPC 结构，都应该为其指定一个 key。

```text
+-----------------+                   +----------------+
|          +---+  |                   |                |
|  Process |key|--|--> identifiery -->|  IPC Metadata  |
|          +---+  |                   |                |
+-----------------+                   +----------------+
```

IPC 结构有两种共享方式：

1. 多个进程通过另外一种机制共同对 key 达成一致认识，使用 key 去操作 IPC。不可以使用相同的 key 重复创建 IPC。
1. 为了避免上述方式中 key 被占用的情况，还提供了一个 Path 的方式进行隔离，Path 有点类似于编程语言中的 namespace，避免命名重复。
   - Linux 提供了一个函数将 Paty 和 ID 转换为一个 key：

   ```cpp
   #include <sys/ipc.h>
   key_t ftok(const char *path, int id);
   ```

   - Path 必须是一个现有文件。

共享内存相比于消息队列，它不会在不同的进程之间进行数据拷贝，因此其性能更高（是最快的一种 IPC）。

共享内存常用 API：

- 获得一个共享存储 identifier:

  ```cpp
  #include <sys/shm.h>

  // size: 共享内存长度，以字节为单位。若创建新共享内存，则 size 必须大于 0，若引用一个现存的共享内存，则 size 指定为 0。
  int shmget(key_t key, size_t size, int flag);
  ```

- 映射到地址空间（将进程内存映射到共享内存）：

  ```cpp
  #include <sys/shm.h>

  // addr 为 0，则连接到内核选择的第一个可用地址上，推荐使用该方式。
  // 映射后，共享内存引用计数加一。
  vlid *shmat(int shmid, const void *addr, int flag);
  ```

- 操作共享内存：

  ```cpp
  #include <sys/shm.h>

  // cmd 为 IPC_RMID 时，删除共享内存。实际上是将引用计数减一。
  int shmctl(int shmid, int cmd, struct shmid_ds *buf);
  ```

Demo:

```cpp
#include <sys/shm.h>

int main(void) {
    int shmid;
    char *shmptr;

    // flag(0600) - user read/write
    shmid = shmget(IPC_PRIVATE, 100000, 0600);

    // 映射到进程地址
    shmptr = shmat(shmid, 0, 0);

    // 删除共享存储短
    shmctl(shmid, IPC_RMID, 0);
}
```
