# Gperftools

- [Heap Checker](heap-checker.md)
- [Heap Profiler](heap-profiler.md)
- [CPU Profiler](cpu-profiler.md)

## 概览

什么是 Gperftools？

> originally Google Performance Tools.

Gperftools 分析主要涵盖了以下三种工具：

工具 | 名称 | 描述
-|-|-
heap-checker | 堆检查器 | 专用的内存泄漏检测工具，对于分析传统的内存泄露很方便，而且可以很好的解决全局对象的析构检测问题。
heap-profiler | 堆分析器 | 非常强大的堆分析工具，可以打印当前堆的分配和释放信息，不同时间段之间的堆变化等。
cpu-profiler | CPU 分析器 |

相比于 valgrind 而言，gperftools 的使用门槛真的要高很多，工具也没 valgrind 的丰富，但是有时候也不得不使用 gperftools：

- valgrind 确实速度比较慢，但是这个不是最关键的；
- valgrind 的工作机制核心是在于拦截系统调用，而在很多场景中（尤其是测试场景、libco 协程场景），用户方会自己修改掉系统调用，这会被 valgrind 拒绝，导致根本无法测试！

## 前置安装

要正常使用 gperftools 真的很麻烦，这里有些前置安装，主要是：

- tcmalloc，这是一个高效内存分配工具，同时可以配合 heap-checker 和 heap-profiler 进行内存泄露探测和分析。
- pprof，将分析结果可视化。

为了简化，下面的安装都是以 `root` 展开。

### 安装 gperftools

gperftools 一共有两个组件：

组件 | 描述
-|-
tcmalloc | 一个高效的内存分配组件，并且是 heap-checker 和 heap-profiler 的关键依赖。
profiler | 进行 CPU 采样分析，是 heap-profiler 的关键依赖。

这两个组件我们都需要进行安装，可参考官方的：[INSTALL](https://github.com/gperftools/gperftools/blob/master/INSTALL) 中的 **Basic Installation** 一节。

对于 Linux64 的机器上，如果直接安装 gperftools 可能是会存在问题的，例如死锁：

> The cpu/heap profiler may be in the middle of malloc, holding some malloc-related locks when they invoke the stack unwinder.  The built-in stack unwinder may call malloc recursively, which may require the thread to acquire a lock it already holds: deadlock.

因此，我们需要先安装 libunwind （但是 gperftools 的 INSTALL 文件中所述，即便安装了 libunwind 可能还是会有问题，对版本的要求也比较苛刻）：

```sh
$ clone https://github.com/libunwind/libunwind.git --branch v1.7.1
$ autoreconf -i
$ ./configure
$ make
```

接着，我们可以正式安装 gperftools 了：

```sh
# 获得 gperftools 安装包并进入目录
$ wget https://github.com/gperftools/gperftools/archive/gperftools-2.8.tar.gz
$ tar -zxvf gperftools-2.8.tar.gz
$ cd gperftools-gperftools-2.8

# 开始安装
$ ./autogen.sh
$ ./configure
$ make
$ make install
```

这个时候，我们就可以在编译二进制代码时，链接 gperftools 的库了：

场景 | 动态库链接示例 | 静态库链接示例
-|-|-
heap-checker | g++ **-Bdynamic** leak.cpp **-ltcmalloc** -g -o leak | g++ **-static** leak.cpp **-ltcmalloc -lunwind** -g -o leak
heap-profiler | g++ **-Bdynamic** leak.cpp **-ltcmalloc** -g -o leak | g++ **-static** leak.cpp **-ltcmalloc -lunwind** -g -o leak
cpu-profiler | g++ **-Bdynamic** leak.cpp **-lprofiler** -g -o leak | g++ **-static** leak.cpp **-lprofiler -lunwind** -g -o leak
both | g++ **-Bdynamic** leak.cpp **-ltcmalloc_and_profiler** -g -o leak | g++ **-static** leak.cpp **-ltcmalloc_and_profiler -lunwind** -g -o leak

**注意：**

- 在 gperftools 在系统中安装好后，其库路径位于系统默认库 `/usr/local/lib/` 或 `/usr/lib/` 中。、
- 静态库需要链接 libunwind.a，否定编译链接会失败。
- 安装的库会包括同名的静态库和动态库，例如：
  ```sh
  libtcmalloc.a
  libtcmalloc.so -> libtcmalloc.so.4.5.5
  libtcmalloc.so.4.5.5
  ```
  - 通过 `-Bdynamic` 可以指定使用动态库。
  - 通过 `-static` 可以指定使用静态库。
  - 如果省略该标识，默认使用的是**动态库**，可参考：[gcc](https://www.rapidtables.com/code/linux/gcc/gcc-l.html)。

### 安装 pprof

安装 pprof 请参考：[google/pprof](https://github.com/google/pprof)。

在安装 pprof 完成后，请检查 PPROF_PATH 环境变量是否正确，如果不正确或没有配置，请进行配置：

```sh
# 先检查下 pprof 路径
$ which pporf
/usr/local/bin/pprof

$ export PPROF_PATH=/usr/local/bin/pprof

# 如果没有正确配置 PPROF_PATH 则在进行相关分析时可能会导致程序符号无法解析。例如下面的告警：
#   The 1 largest leaks:
#   *** WARNING: Cannot convert addresses to symbols in output below.
#   *** Reason: Cannot run 'pprof' (is PPROF_PATH set correctly?)
#   *** If you cannot fix this, try running pprof directly.
#   Leak of 16 bytes in 1 objects allocated from:
#           @ 400681 
#           @ 7fc1d593cc05 
#           @ 4005b9 
#           @ 0 
```

## 快速开始

为方便快速会议和使用，这里列出使用方法。

### heap-checker

首先是编译时链接 tcmalloc：

```sh
g++ leak.cpp -ltcmalloc -g -o leak
```

运行 HEAPCHECK 检查 leak 程序的内存泄露情况：

```sh
# 环境变量含义：
# HEAP_CHECK_DUMP_DIRECTORY=.                 将 heap-profile 文件输出到当前目录
# LD_PRELOAD="/usr/local/lib/libtcmalloc.so"  指定链接的 tcmalloc 动态库
# HEAPCHECK=normal                            使用 normal flavor 运行
$ env HEAP_CHECK_DUMP_DIRECTORY=. LD_PRELOAD="/usr/local/lib/libtcmalloc.so" HEAPCHECK=normal ./leak

# 根据 HEAPCHECK 提示进行打印
$ pprof ./leak "./leak.18831._main_-end.heap" --inuse_objects --lines --heapcheck  --edgefraction=1e-10 --nodefraction=1e-10 --svg > leak.svg
$ pprof ./leak "./leak.18831._main_-end.heap" --inuse_objects --lines --heapcheck  --edgefraction=1e-10 --nodefraction=1e-10 --text
```

### wexin heap-checker

微信环境下使用，首先是将 tcmalloc 编译进去，这里是静态链接：

```BUILD
cc_binary(
  name = "heap_checker_test",
  srcs = [
    "heap_checker_test.cc",
  ],
  copts = [
    "-g",
    "-std=c++11",
  ],
  deps = [
    "//mm3rd/gperftools:tcmalloc",
  ],
  linkstatic = True,
)
```

运行代码时，需要使用 strict flavor。不知道为什么，用 'normal' 总是会失败：

```sh
$ env HEAP_CHECK_DUMP_DIRECTORY=. HEAPCHECK=strict ./heap_checker_test

$ pprof ./heap_checker_test "./heap_checker_test.14849._main_-end.heap" --inuse_objects --lines --heapcheck  --edgefraction=1e-10 --nodefraction=1e-10 --svg > leak.svg
$ pprof ./heap_checker_test "./heap_checker_test.14849._main_-end.heap" --inuse_objects --lines --heapcheck  --edgefraction=1e-10 --nodefraction=1e-10 --text
Total: 5 objects
       5 100.0% 100.0%        5 100.0% leak /data/.../test/heap_checker_test.cc:8
       0   0.0% 100.0%        5 100.0% __libc_start_main ??:0
       0   0.0% 100.0%        5 100.0% _start ??:0
       0   0.0% 100.0%        5 100.0% main /data/.../test/heap_checker_test.cc:30
       0   0.0% 100.0%        5 100.0% test /data/.../test/heap_checker_test.cc:14
```

## 附录：痛苦的 tcmalloc 安装

tcmalloc 由于历史原因，存在两个库：

- [google/gperftools](https://github.com/gperftools/gperftools) 中的 tcmalloc 子集。
- [google/tcmalloc](https://github.com/google/tcmalloc)。

`google/tcmalloc` 的 gperftools 的安装有个硬伤：对 GCC 的版本要求很高：

> GCC 9.2 or higher is required.

多数情况下我们没有这样的条件，同时，google/tcmalloc 中没有 profiler 组件，无法作 cpu profile，因此我直接放弃了安装 `google/tcmalloc`。

## 附录：参考文献

1. [gperftools](https://gperftools.github.io/gperftools/)
1. [gperftools/gperftools](https://github.com/gperftools/gperftools)
1. [google/tcmalloc](https://github.com/google/tcmalloc)
1. [google/pprof](https://github.com/google/pprof)
1. [内存泄漏分析的利器 —— gperftools 的 Heap Checker](https://cloud.tencent.com/developer/article/1383795)
