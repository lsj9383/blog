# TSF4G Connection & Bus

<!-- TOC -->

- [TSF4G Connection & Bus](#tsf4g-connection--bus)
    - [Overview](#overview)
    - [Tconnd](#tconnd)
        - [Tconnd TFRAME](#tconnd-tframe)
    - [TBus](#tbus)
    - [Appendix: Shared Memory](#appendix-shared-memory)

<!-- /TOC -->

## Overview

Tsf4g是 一套整个的游戏解决方案，囊括接入层，到逻辑srv的应用框架，到网络通讯的编码格式以及通信方式，后端数据存储等。

这里主要介绍接入层 Tconnd 和进程通信组建 TBus。

Tconnd、TBus 整体定位下图一言以蔽之：

![system.png](assets/system.png)

## Tconnd

Tconnd 为 Game Server 提供接入服务，使逻辑层不再关心网络层数据收发和连接管理。

Tconnd 有多种工作模式（例如 TDR 模式、QQ 模式、WEB 模式），现在主流采用的是 GCP 模式。

**注意：**

- GCP 指的是 General Communication Protocol，通用通信协议。
- TDR 指的是 TSF4G Data Represention，互娱研发部自研跨平台多语言数据表示组件，主要用于基于数据的序列化反序列化（支持二进制方式和 XML 文本方式）以及 ORM 数据存储。

Tconnd 在 GCP 模式中，可以在建立连接时校验 Client，如下图所示：

![tconnd-system](assets/tconnd-system.png)

上图中，还存在一个特殊的 APS(AuthProxy Servic)，Tconnd 通过 TCP 协议将 Client 凭证传递给 APS，由 APS 对凭证进行校验。

这些 Client 凭证用于标识用于，可以是：

- QQ 票据
- Wechat 授权码
- Wechat Refresh Token（免登录）
- JWT
- 其他

除此外，Tconnd GCP 也具有加密通信的能力：通过 DH 协商机制，消息加密，消息压缩​。

### Tconnd TFRAME

FRAME 协议是 TCONND 定义，用于 TCONND 进程与后台服务进程通信的消息格式，包含两个部分：

- TFRAMEHEAD，消息头部。
- TFRAMECMDDATA，消息负载。

在代码中，TFRAMECMDDATA 是 TFRAMEHEAD 的一部分。

**注意：**

- TFRAMEHEAD 中不会包含 TFRAMECMDDATA 的长度
- TFRAMEHEAD 的结构是固定的，长度也是固定的，只需要用消息长度剪掉 TFRAMEHEAD 长度，即是 TFRAMECMDDATA 长度。

## TBus

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
