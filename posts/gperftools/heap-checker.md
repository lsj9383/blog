# Gperftools: Heap Checker

[TOC]

## 概览

在 C++ 程序中，我们可以使用 gperftools 提供的 heap-checker 工具，探测内存泄露问题。

要使用 heap-checker 进行内存泄露探测，有以下三个步骤：

1. C++ 程序链接 tcmalloc 库；
1. 运行你的程序；
1. 分析输出。

## 链接 TCMalloc

> 在链接 TCMalloc 前请安装你的 tcmalloc，可参考 [前置安装](readme.md)。

heap-checker 是 tcmalloc 的一部分，因此要在程序中使用 heap-checker 需要：

- 先链接 tcmalloc：`-ltcmalloc`；
- 并在运行时添加环境变量 `LD_PRELOAD="/usr/lib/libtcmalloc.so"`，以使得插入 tcmalloc heap-checker 的代码。

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

进行内存泄露检测有两种模式：

模式 | 描述 | 无侵入性 | 灵活性
-|-|-|-
whole-program | 又叫做**隐式检查**，这种模式可以自动的对整个程序进行内存泄露检测，并且不需要修改代码。 | 高 | 低
partial-program | 又叫做**显式检查**，这种模式可以通过代码来指定检查哪个部分的内存泄露。 | 低（需要改代码）| 高

**注意：**

- 个人经验中，感觉 whole-program 不太稳定，有时候不能正常检测。甚至 main 函数的入参格式也会带来影响，最好用 partial-program。

对于 `whole-program` 模式，内存泄露检测还有四种 Flavors：

Flavors | 描述 | 使用场景
-|-|-
minimal | 尽可能晚的进行内存跟踪，因此如果在全局构造函数中（main 之前执行）存在内存泄露，那么将感知不到。 | 粒度比较粗糙，需要明确忽略全局初始化中的内存泄露时才使用该模式。
normal | 跟踪存活的对象，并在程序结束时，如果这些对象不可达则进行报告。 | **日常 heap-checker 使用**，但是可能会漏报。
strict | 和 'normal' 是类似的，但是会做一些额外的检查。这里指的额外检查是程序启动和退出时的内存泄露情况。 | 比 normal 更全面，且不易错报。**其实我感觉 strict 比 normal 好用**。
draconian | 根本不检查是否为活跃对象（程序运行期间的可访问内存），只要在程序退出时还存在的对象就会报告内存泄露。 | 对精度要求高的场景。
as-if | 一种额外的 flavor，非常灵活，可以对 heap-checker 细节控制。 | 需要非常高精度的调优场景。
local | 一种额外的 flavor，告诉 heap-checker 使用 partial-program，而不是 whole-program。 | 使用 partial-program 模式。

对于 strict：

> ChatGPT：在程序运行过程中，如果有全局变量在程序运行过程中分配了内存，但在全局析构函数中“遗忘”了这些内存（例如将指向内存的指针设置为 NULL，而没有释放内存），那么在 "strict" 模式下，heap-checker 会提示内存泄漏的信息，而在 "normal" 模式下则不会。这是因为在 "strict" 模式下，heap-checker 会检查程序退出时所有的内存分配和释放操作，包括全局变量中的内存分配和释放。如果发现有内存泄漏的情况，heap-checker 会输出相应的信息，以帮助用户定位和解决内存泄漏问题。

### 隐式检查（Whole-program）模式

可以使用 "whole program" 模式进行内存分析。这里 "whole program" 的含义是：

- heap-checker 将在进入 `main()` 函数开始前就进行内存分配的追踪。
- heap-checker 在程序退出时再次检查。

如果发现内存泄露，会终止程序（exit(1)），并打印一条如何追踪该内存泄露的消息。

**注意：**

- 使用 heap-checker 会记录每个分配的追踪信息，这可能导致程序速度减慢，以及内存使用量的上升。

通过环境变量 `HEAPCHECK`，我们可以启动 "whole program" 模式的内存泄露检测：

```sh
# 需要提前设置环境变量 export LD_PRELOAD=/usr/local/lib/libtcmalloc.so
# env HEAPCHECK=normal /usr/local/bin/my_binary_compiled_with_tcmalloc
$ env HEAPCHECK=normal {binary}

# 也可以同时设置环境变量：LD_PRELOAD 和 HEAPCHECK
$ env LD_PRELOAD="/usr/local/lib/libtcmalloc.so" HEAPCHECK=normal {binary}
```

一个示例（[leak.cpp](demo/leak.cpp)）：

```sh
# 编译：
$ g++ leak.cpp -ltcmalloc -g -o leak

# 运行
$ env LD_PRELOAD="/usr/local/lib/libtcmalloc.so" HEAPCHECK=normal ./leak

# 输出：
#   WARNING: Perftools heap leak checker is active -- Performance may suffer
#   Have memory regions w/o callers: might report false leaks
#   Leak check _main_ detected leaks of 16 bytes in 1 objects
#   The 1 largest leaks:
#   Using local file ./leak.
#   Leak of 16 bytes in 1 objects allocated from:
#           @ 400681 main
#           @ 7f4b6f5dbc05 __libc_start_main
#           @ 4005b9 _start
#           @ 0 _init
```

### 显示检查（Partial-program）模式

除了使用 whole-program 模式外，我们还可以指定明确希望进行内存泄露的代码段，而不用检查整个程序。

> This check verifies that between two parts of a program, no memory is allocated without being freed.

要使用这种 partial-program 模式，需要：

1. 引用头文件：`<gperftools/heap-checker.h>`；
1. 在希望检查的代码段前，构造 HeapLeakChecker 对象；
1. 在希望检查的代码段尾，调用 HeapLeakChecker 对象的 NoLeaks() 方法；
1. 使用 `HEAPCHECK=local` 进行 partial-program 的内存探测。

这是一个官方示例：

```cpp
// "test_foo" 会影响最终 heap leak 分析文件的命名
HeapLeakChecker heap_checker("test_foo");
{
  // code that exercises some foo functionality;
  // this code should not leak memory;
}
if (!heap_checker.NoLeaks()) assert(NULL == "heap memory leak");
```

上面只会加入内存检测的代码，并不会真的进行内存检测，实际启用还是需要通过环境变量来：

```sh
# $ env LD_PRELOAD="/usr/local/lib/libtcmalloc.so" HEAPCHECK=local {binary}
$ env HEAPCHECK=local {binary}
```

如果你还想继续使用 whole-program 模式，则将 `local` 修改为 `normal` 即可。

### 禁用内存泄露

如果代码中存在已知的内存泄露，希望暂时规避。可能的原因有：

- 可能是历史债务难以修改，通过定期重启进程的方式来解决；
- 不影响观察其他内存泄露问题。

那么我们可以将这部分代码禁用内存泄露。我们只需要使用 `HeapLeakChecker::Disabler` 对象即可：

```cpp
{
  HeapLeakChecker::Disabler disabler;
  // <leaky code>
}
```

### 长期运行检查

在很多情况下，一个程序并不会立即执行完，尤其是长期运行在服务器上的后台程序。对于这类需要长期运行的程序，如何进行内存泄露检测呢？

在 heap-checker 中，提供了 `HeapLeakChecker::NoGlobalLeaks()` 方法，以便于程序运行中进行内存泄露检测。执行该方法时就会打印一次内存检测报告。

一个示例：

```cpp
for (int i; i < 5; ++i) {
  // <leaky code>
  sleep(1);

  // 每次执行 HeapLeakChecker::NoGlobalLeaks() 都会打印一次内存报告
  if (!HeapLeakChecker::NoGlobalLeaks()) {
    // <catch leak error>
  }
}
```

### 精确控制 HEAPCHECK

我们可以通过环境变量来精确控制 HEAPCHECK 的行为：

环境变量 | 默认值 | 描述
-|-|-
HEAP_CHECK_IDENTIFY_LEAKS | False | 如果为 true，则会在 heap-profile 文件中生成泄露对象的地址。
HEAP_CHECK_TEST_POINTER_ALIGNMENT | False | 如果为 true，检查所有的内存泄露，判断是否是由于未对其的指针导致。
HEAP_CHECK_POINTER_SOURCE_ALIGNMENT | sizeof(void*) | 内存中的所有地址都应该进行对齐。如果不需要对齐（任何对齐都可以），则使用 1。
PPROF_PATH | pprof | pprof 可执行文件位置。
HEAP_CHECK_DUMP_DIRECTORY | /tmp | heap-profile 文件的保存目录。可以使用工作目录，即 "HEAP_CHECK_DUMP_DIRECTORY=."

对于 HEAP_CHECK_TEST_POINTER_ALIGNMENT 的更多解读：

> ChatGPT: 在 C/C++ 中，指针需要被正确地对齐，否则可能会导致不可预测的行为，例如程序崩溃、数据损坏等。默认情况下，heap-checker 只检查内存泄漏和非法内存访问，而不检查指针对齐的情况。但是，如果在程序中使用了不对齐的指针，可能会导致内存泄漏或非法内存访问的问题。

也就是说，如果没使用 HEAP_CHECK_TEST_POINTER_ALIGNMENT，当发生了未对齐问题时，可能提示信息很难看出来。通过这个方法可以明确问题原因是未对其地址所致。

**仅对于 whole-program** 的运行生效的环境变量：

环境变量 | 默认值 | 描述
-|-|-
HEAP_CHECK_MAX_LEAKS | 20 | 指定打印到 stderr 的内存泄露事件的数量。如果是负数或者零，将打印所有的内存泄露到 stderr。<br>**注意：** 不影响打印到 heap-profile 文件中的内存泄漏问题。所有的内存泄露都会输出到 heap-profile 文件中。

HEAP_CHECK_MAX_LEAKS 是指的一次性打印到 stderr 中的内存泄露事件。如果使用 `HeapLeakChecker::NoGlobalLeaks()` 是会打印多次到 stderr 的，但是每次打印到 stderr 的时候内存事件都只会最多有 HEAP_CHECK_MAX_LEAKS 个。

**仅对于 whole-program 的 as-if** 的运行生效的环境变量：

环境变量 | 默认值 | 描述
-|-|-
HEAP_CHECK_AFTER_DESTRUCTORS | False | 如果为 True，则在所有的全局析构函数执行完成后进行内存泄露检查。如果为 False，则在所有的 REGISTER_HEAPCHECK_CLEANUP 执行后检查，这通常在全局析构函数执行之前进行。
HEAP_CHECK_IGNORE_THREAD_LIVE | True | 如果为 True，忽略线程栈（Thread Stacks）和寄存器的对象（即便这些数据有泄露报告，也忽略掉）。
HEAP_CHECK_IGNORE_GLOBAL_LIVE | True | 如果为 True，忽略可达的全局变量和数据（即便这些数据有泄露报告，也忽略掉）。

## 分析输出

使用 heap-checker 运行程序时，会得到两部分的输出：

- stderr
- heap-profile

### 输出到 stderr

当使用 HEAPCHECK 时，将会在检测到内存泄露时将泄露信息输出到 stderr 中，例如：

```sh
$ env HEAP_CHECK_DUMP_DIRECTORY=. LD_PRELOAD="/usr/local/lib/libtcmalloc.so" HEAPCHECK=normal ./leak
```

其中有三个重要的信息：

- 内存泄露位置：
  ```sh
  Leak check _main_ detected leaks of 13 bytes in 6 objects
  The 2 largest leaks:
  Using local file ./leak.
  Leak of 8 bytes in 1 objects allocated from:
          @ 400b44 main
          @ 7fc05103cc05 __libc_start_main
          @ 400a59 _start
          @ 0 _init
  Leak of 5 bytes in 5 objects allocated from:
          @ 400b1a test
          @ 400b90 main
          @ 7fc05103cc05 __libc_start_main
          @ 400a59 _start
          @ 0 _init
  ```

- 如何进一步分析：
  ```sh
  If the preceding stack traces are not enough to find the leaks, try running THIS shell command:

  pprof ./leak "./leak.18831._main_-end.heap" --inuse_objects --lines --heapcheck  --edgefraction=1e-10 --nodefraction=1e-10 --gv
  # 这里有个问题，对于使用 Linux Console 时，直接使用 --gv 是没法打印的，需要转换成 svg
  # pprof ./leak "./leak.18831._main_-end.heap" --inuse_objects --lines --heapcheck  --edgefraction=1e-10 --nodefraction=1e-10 --svg
  ```

- HEAPCHECK 环境变量调整：
  ```sh
  If you are still puzzled about why the leaks are there, try rerunning this program with HEAP_CHECK_TEST_POINTER_ALIGNMENT=1 and/or with HEAP_CHECK_MAX_POINTER_OFFSET=-1
  If the leak report occurs in a small fraction of runs, try running with TCMALLOC_MAX_FREE_QUEUE_SIZE of few hundred MB or with TCMALLOC_RECLAIM_MEMORY=false, it might help find leaks more repeatably
  ```

### 输出到 heap-profile

首先，对于输出的 heap-profile 文件，我们可以打印出一共存在哪些内存泄露：

```sh
# pprof --text <binary> <heap-profile>
$ pprof --text leak /tmp/leak.27118._main_-end.heap
Total: 0.0 MB
     0.0  61.5%  61.5%      0.0 100.0% main
     0.0  38.5% 100.0%      0.0  38.5% test
     0.0   0.0% 100.0%      0.0 100.0% __libc_start_main
     0.0   0.0% 100.0%      0.0 100.0% _start
```

其次，最重要的是我们可以用来输出内存泄露的 callgraph（这个命令其实就是 HEAPCHECK 运行完成后，stderr 中输出的）：

```sh
# pprof <binary> <heap-profile> --inuse_objects --lines --heapcheck  --edgefraction=1e-10 --nodefraction=1e-10 --svg > <svg-file>
# 得到内存泄漏的 callgraph svg：
$ pprof ./leak "./leak.9136._main_-end.heap" --inuse_objects --lines --heapcheck  --edgefraction=1e-10 --nodefraction=1e-10 --svg > leak.svg

# 如果感觉打印到 svg 上面看不方便，还可以直接输出到控制台中看：
$ pprof ./leak "./leak.9136._main_-end.heap" --inuse_objects --lines --heapcheck  --edgefraction=1e-10 --nodefraction=1e-10 --text
Using local file ./leak.
Using local file ./leak.9136._main_-end.heap.
Total: 6 objects
       5  83.3%  83.3%        5  83.3% test /data/learn/heap-checker/leak-loop.cpp:8
       1  16.7% 100.0%        1  16.7% main /data/learn/heap-checker/leak-loop.cpp:13
       0   0.0% 100.0%        6 100.0% __libc_start_main ??:0
       0   0.0% 100.0%        6 100.0% _start ??:0
       0   0.0% 100.0%        5  83.3% main /data/learn/heap-checker/leak-loop.cpp:17
```

这个 callgraph 其实本质上就是内存分配时刻的函数栈的记录，但是实际上在显示时不会按实际情况打印函数栈，而是会根据实际情况做聚合。

最后，在 HEAPCHECK 场景中，其实 heap-profile 的文件名不是太重要，因为运行完后总是会输出文件名的。这里有个简单的规则：

```text
{HEAP_CHECK_DUMP_DIRECTORY}/leak.{PID}._main_-end.heap
```

另外，这个 callgraph 中只会显示内存泄露的对象，对于正常回收、有指针正常引用的对象不会显示出来。

## 问题定位

当检测出内存泄露后应该怎么做？

- 首先，应该运行报告中的 pprof 命令。
- 接着，判断是否真的存在泄露：
  - 如果存在泄露就修复它。
  - 如果是可以忽略的，就用 `HeapLeakChecker::Disabler` 来关闭掉这部分的检查。
- 最后，做到 heap-checker cleanup。

更多信息可参考：[heap-checking using tcmalloc](https://gperftools.github.io/gperftools/heap_checker.html)

## 参考文献

1. [heap-checking using tcmalloc](https://gperftools.github.io/gperftools/heap_checker.html)
1. [tcmalloc](https://github.com/google/tcmalloc)
