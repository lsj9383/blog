# Heap Profiler

[TOC]

## 概览

Gperftools 提供了堆分析器 heap-profiler，用于探索 C++ 程序对内存的管理。这个工具可以：

- 展现任何给定时间的堆上的内存分配情况。
- 定位内存泄露情况（对于内存泄露，最好还是用 heap-checker）。
- 寻找进行了大量内存分配的地方。

heap-profiler 会记录所有的内存分配和释放情况，并跟踪每个内存分配点（Allocation Site）的各种信息。

这里的分配点（Allocation Site）指的是：

> An allocation site is defined as the active stack trace at the call to malloc, calloc, realloc, or, new.

和 heap-checker 是类似的，使用 heap-profiler 也是分为三步：

1. C++ 程序链接 tcmalloc 库；
1. 运行你的程序；
1. 分析输出。

**注意：**

- heap-profiler 对于定位传统的内存堆没有释放的问题是比较乏力的，主要原因是没有针对全局对象的处理手段：
  - 全局对象，可能会在构造函数或者运行时进行堆分配，而这些分配的内存是在全局析构时释放。
  - 全局析构，是在程序退出的时刻执行的，而 heap-profiler 的统计输出是在全局析构执行前。
  - 因此，如果使用 heap-profiler 来判断内存泄露，可能会将稍后正常释放的内存也会统计进去。

## 链接 TCMalloc

> 在链接 TCMalloc 前请安装你的 tcmalloc，可参考 [前置安装](readme.md)。

heap-profiler 是 tcmalloc 的一部分，因此要在程序中使用 heap-checker 需要：

- 先链接 tcmalloc：`-ltcmalloc`；
- 并在运行时添加环境变量 `LD_PRELOAD="/usr/lib/libtcmalloc.so"`，以使得插入 tcmalloc heap-profiler 的代码。

这是一个例子（[leak.cpp](demo/leak.cpp)）：

```sh
# 编译并链接 tcmalloc
$ g++ leak.cpp -ltcmalloc -g -o leak

# 此时检查 leak 的链接情况，其实是找不到 tcmalloc 的：
# $ ldd leak
#         linux-vdso.so.1 =>  (0x00007ffdbb1b3000)
#         /$LIB/libonion.so => /lib64/libonion.so (0x00007f5a31a41000)
#         libtcmalloc.so.4 => not found
#         libstdc++.so.6 => /usr/local/lib64/libstdc++.so.6 (0x00007f5a31616000)
#         libm.so.6 => /lib64/libm.so.6 (0x00007f5a31314000)
#         libgcc_s.so.1 => /usr/local/lib64/libgcc_s.so.1 (0x00007f5a310fd000)
#         libc.so.6 => /lib64/libc.so.6 (0x00007f5a30d39000)
#         libdl.so.2 => /lib64/libdl.so.2 (0x00007f5a30b35000)
#         /lib64/ld-linux-x86-64.so.2 (0x00007f5a31928000)

# 指定环境变量
$ export LD_PRELOAD=/usr/local/lib/libtcmalloc.so 

# 此时检查 leak 的链接情况，可以找到 tcmalloc 了：
# $ ldd leak
#         linux-vdso.so.1 =>  (0x00007ffffc554000)
#         /usr/local/lib/libtcmalloc.so (0x00007fe41de3d000)
#         /$LIB/libonion.so => /lib64/libonion.so (0x00007fe41e355000)
#         libstdc++.so.6 => /usr/local/lib64/libstdc++.so.6 (0x00007fe41db2b000)
#         libm.so.6 => /lib64/libm.so.6 (0x00007fe41d829000)
#         libgcc_s.so.1 => /usr/local/lib64/libgcc_s.so.1 (0x00007fe41d612000)
#         libc.so.6 => /lib64/libc.so.6 (0x00007fe41d24e000)
#         libunwind.so.8 => /lib64/libunwind.so.8 (0x00007fe41d034000)
#         libz.so.1 => /lib64/libz.so.1 (0x00007fe41ce1e000)
#         libpthread.so.0 => /lib64/libpthread.so.0 (0x00007fe41cc02000)
#         libdl.so.2 => /lib64/libdl.so.2 (0x00007fe41c9fe000)
#         /lib64/ld-linux-x86-64.so.2 (0x00007fe41e23d000)
```

## 运行你的程序

有两种方式启动 heap-profiler：

方式 | 描述 | 无侵入性 | 灵活性
-|-|-|-
隐式启动 | 通过环境变量的形式，可以启动 heap-profiler。 | 高 | 低
显式启动 | 通过代码的方式，指明进行堆分析的代码段。 | 低 | 高

### 隐式启动

通过 `HEAPPROFILE` 环境变量可以指定 heap-profiler 的分析输出结果，当指定该环境变量后，就可以自动开启堆分析。

一个示例（[leak.cpp](demo/leak.cpp)）：

```sh
# 需要提前设置环境变量 export LD_PRELOAD=/usr/local/lib/libtcmalloc.so
# $ env HEAPPROFILE=<heap-profile> <binary>
$ env HEAPPROFILE="./myleak.prof" ./leak

# 也可以同时设置环境变量：LD_PRELOAD 和 HEAPCHECK
# $ env LD_PRELOAD="/usr/local/lib/libtcmalloc.so" HEAPPROFILE=<heap-profile> <binary>
$ env LD_PRELOAD="/usr/local/lib/libtcmalloc.so" HEAPPROFILE="./myleak.prof" ./leak
```

### 显式启动

在代码中，将希望进行 heap-profiler 的代码使用 `HeapProfilerStart()` 和 `HeapProfilerStop()` 包围起来（这两个函数的声明位于头文件：`<gperftools/heap-profiler.h>`）。

如果在 HeapProfilerStop() 前，需要打印堆的快照，可以使用（需要注意，使用 HeapProfilerStop() **不会自动存储堆快照信息**）：

- `HeapProfilerDump()`，这会将当前的堆使用情况输出到 heap-profile 中。
- `GetHeapProfile()`，可以在程序中拿到堆情况的字符串，根据用户自己的意愿输出到期望的位置。

为了程序自动知晓当前是否处于 heap-profiler 的分析中，可以使用 `IsHeapProfilerRunning()`。

一个示例：

```cpp
#include <gperftools/heap-profiler.h>

{
  // "start" 是 heap-profile 分析文件的前缀
  HeapProfilerStart("start");
  {
    // <code>
  }
  // "end" 没啥用，只是一个打印到 stderr 的提示而已，表示因为什么原因进行了一次存储堆快照
  HeapProfilerDump("end");
  HeapProfilerStop();
}
```

**注意：**

- 这里 HeapProfilerDump 的参数 "end" 表示的是堆快照输出的事件原因，打印到 stderr。

例如，当分配的内存超过 HEAP_PROFILE_ALLOCATION_INTERVAL 时就会进行一次打印，此时会输出打印原因：

```sh
# ... 这里假设超过 5M 进行一次打印...
Starting tracking the heap
Dumping heap profile to start.0001.heap (15 MB allocated cumulatively, 15 MB currently in use)
Dumping heap profile to start.0002.heap (26 MB allocated cumulatively, 26 MB currently in use)
Dumping heap profile to start.0003.heap ()
```

### 修改运行时行为

我们可以通过环境变量，调整运行时 heap-profiler 的行为：

环境变量 | 默认值 | 描述
-|-|-
HEAP_PROFILE_ALLOCATION_INTERVAL | 1Gb | 每当申请了多少 bit 数据时会自动打印一次堆快照。
HEAP_PROFILE_INUSE_INTERVAL | 100Mb
HEAP_PROFILE_TIME_INTERVAL | 0 | 每当经过多少秒进行一次堆快照打印。如果为 0 代表不使用定时输出。
HEAPPROFILESIGNAL | Disabled | 每当收到什么信号，进行一次堆快照打印。
HEAP_PROFILE_MMAP | False | 是否开启追踪 mmap / mremap / sbrk 的调用情况（不影响 malloc、calloc、realloc、new 的追踪）。<br>**注意：** 会有多余的追踪，因为 tcmalloc 内部使用了 mmap 和 sbrk 进行内存分配。一种解决方法是 pprof 分析是过滤掉：`pprof --ignore='DoAllocWithArena|SbrkSysAllocator::Alloc|MmapSysAllocator::Alloc`。
HEAP_PROFILE_ONLY_MMAP | False | 是否**仅**记录 mmap / mremap / sbrk 的调用情况。开启后，将不会跟踪 malloc、calloc、realloc、new 的调用情况。
HEAP_PROFILE_MMAP_LOG | False | 是否记录 mmap / munmap 的调用情况。

## 分析输出

输出的文件命名格式如下：

```txt
<prefix>.<n>.heap
```

参数 | 隐式场景 | 显式场景
-|-|-
prefix | 是通过环境变量 "HEAPPROFILE" 指定的 | 是通过 `HeapProfilerStart(<prefix>)` 的参数指定的。
n | 是输出的第几个快照文件。 | 是输出的第几个快照文件。

### 统计口径

其实生成的 heap-profile 文件中包括了非常多的信息：

- 当前堆空间内存分配的信息（字节数、对象数）。
- 当前堆空间内存释放的信息（字节数、对象数）。

默认情况下，统计的是堆空间内存分配的字节数，释放的不会算进去。但是这个统计口径是可以在使用 pprof 时变化的：

Flags | 默认 | 描述
-|-|-
--inuse_space | √ | 显示**正在使用**的字节数，单位 MB（即已分配但未释放的空间）。
--inuse_objects | | 显示**正在使用**的对象数量（即已分配但未释放的对象数量）。
--alloc_space | | 显示分配的字节数，单位 MB。这包括此后已取消分配的空间。如果您想查找程序中的主要分配站点，请使用此选项。
--alloc_objects | | 显示已分配对象的数量。这包括此后已解除分配的对象。如果您想查找程序中的主要分配站点，请使用此选项。

### 文本输出

文本输出是最简单的方式：

```sh
$ pprof --text gfs_master /tmp/profile.0100.heap
   255.6  24.7%  24.7%    255.6  24.7% GFS_MasterChunk::AddServer
   184.6  17.8%  42.5%    298.8  28.8% GFS_MasterChunkTable::Create
   176.2  17.0%  59.5%    729.9  70.5% GFS_MasterChunkTable::UpdateState
   169.8  16.4%  75.9%    169.8  16.4% PendingClone::PendingClone
    76.3   7.4%  83.3%     76.3   7.4% __default_alloc_template::_S_chunk_alloc
    49.5   4.8%  88.0%     49.5   4.8% hashtable::resize
```

列 | 描述
-|-
最后一列（第 6 列） | 这些函数代表的是内存分配点所位于的函数（即分配点）。
第 1 列 | 分配点**直接**分配的内存（MB）
第 2 列 | 分配点直接分配的内存栈所有内存的百分比。
第 3 列 | 第二列的累计和。感觉这个不太重要。
第 4 列 | 分配点及其子分配点的内存和（MB）
第 5 列 | 该分配点及其子分配点的内存和占所有内存的百分比。

**注意：**

- 有时候第一列，第四列会显示 0，可能是因为这里的显示是单位 MB，而有时候内存申请的太少，就四舍五入掉了。
- 如果没有申请任何堆内存，或者所有堆内存都被释放掉了，这里不会打印分配点表格。

### callgraph

相比于文本，我们可以输出更加直观的图形：

```sh
% pprof gfs_master /tmp/profile.0100.heap --svg > gfs_master.svg
```

![](assets/heap-example1.png)

### 比较 heap-profile

比较两个不同时间段的 heap-profile 是非常有意义的：

- 耐久性测试：长时间运行的服务是否存在内存不断累积的情况？如果存在，是哪里在累积，是否合理。
- 难以发现的非传统内存泄露：这可能是因为对象不用了，但是仍然握有指针所致，其实应该剔除掉。
- 跳过某个阶段发现内存问题。

下面的示例中，将会使用 0100 的内存使用量减去 0004 的内存使用量，进而发现 0004 --> 0100 这段期间的内存分配情况：

```sh
$ pprof gfs_master --base=/tmp/profile.0004.heap /tmp/profile.0100.heap --text
$ pprof gfs_master --base=/tmp/profile.0004.heap /tmp/profile.0100.heap --svg > gfs_master.svg
```

### 忽略和关注特定区域

能想到的是，对于一个大型程序，必然 heap-profiler 可能会相当大，因为其堆空间申请了各种各样的内存（这里特指的是程序运行期间的）。

其中大量的内存分配代码可能是历史债务也好，可能是框架和库的也好，可能是其他人的也好，总之，都是我们在我们控制之外的。为了更加聚焦于我们需要关注的内容，我们可以设置忽略或者关注特定的分配点。

- 设置特定关注的分配点（匹配规则：callgraph 路径匹配正则表达式）：
  ```sh
  $ pprof --focus=DataBuffer gfs_master /tmp/profile.0100.heap --text
  ```
- 设置忽略的分配点（匹配规则：callgraph 路径匹配正则表达式）：
  ```sh
  $ pprof --ignore=DataBuffer gfs_master /tmp/profile.0100.heap --text
  ```

## 参考文献

## 参考文献

1. [heap-profiler using tcmalloc](https://gperftools.github.io/gperftools/cpuprofile.html)
