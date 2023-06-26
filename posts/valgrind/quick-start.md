# 快速开始

[TOC]

## 概述

> 本文主要参考 [The Valgrind Quick Start Guide](https://valgrind.org/docs/manual/quick-start.html)。

Valgrind 工具套件提供了一系列的调试和分析工具帮助你编写更快且更正确的程序。其中，Valgrind 使用的最多的工具就是 Memcheck，它能帮助你定为大多数内存相关的错误。

## 准备你的程序

为了便于 Valgrind 更好的帮助你定位问题，可以考虑这些编译选项：

- `-g` 选项：强烈推荐使用，这将包含调试信息，便于 Valgrind 直接定位到代码行。
- `-O0` 选项：如果你可以容忍运行速度变慢，也是一个好主意。
- `-O1` 选项：相比于 -00，该选项的性能更好，但是行号可能不准确。
- `-O2` 选项：不建议使用，会存在误报。

## 在 Memcheck 下运行程序

如果你是这样执行程序的：

```sh
$ myprog arg1 arg2
```

在 Memcheck 下应该这么执行：

```sh
$ valgrind --leak-check=yes myprog arg1 arg2
```

Memcheck 是默认的 Valgrind 工具，而 `--leak-check=yes` 开启了内存泄露检查器。

您的程序将比正常运行速度慢得多（例如 20 到 30 倍），Memcheck 将发出有关其检测到的内存错误和泄漏的消息。

## Memcheck 的输出

这是一个 C 语言例子：

```c
// a.c

#include <stdlib.h>

void f(void)
{
    int* x = malloc(10 * sizeof(int));
    x[10] = 0;        // problem 1: heap block overrun
}                    // problem 2: memory leak -- x not freed

int main(void)
{
    f();
    return 0;
}
```

该 C 语言代码存在两个错误：

- 堆溢出
- 内存泄露

编译该 C 语言文件：

```sh
$ gcc -g a.c -o ac
```

然后进行内存问题检测：

```sh
$ valgrind --leak-check=yes ./ac
```

你可能首先会看到堆溢出的错误信息：

```sh
==19182== Invalid write of size 4
==19182==    at 0x804838F: f (a.c:6)
==19182==    by 0x80483AB: main (a.c:11)
==19182==  Address 0x1BA45050 is 0 bytes after a block of size 40 alloc'd
==19182==    at 0x1B8FF5CD: malloc (vg_replace_malloc.c:130)
==19182==    by 0x8048385: f (a.c:5)
==19182==    by 0x80483AB: main (a.c:11)
```

这里表示：

- 在每条错误信息中，都包含较多细节，请仔细阅读。
- 19182 是进程 ID。
- 第一行（"Invalid write..."）告诉你发生的错误类型。在这里，由于堆块溢出，程序写入了一些不应该写入的内存。
- 第一行下方是堆栈跟踪，方便告诉你问题发生在哪里。
  - 堆栈跟踪可能会变得相当大并且令人困惑，尤其是在使用 C++ STL 时。
  - 从下往上阅读它们会有所帮助。
  - 如果堆栈跟踪不够大，请使用--num-callers选项使其更大。
- 代码地址（例如 `0x804838F`）通常不重要，但有时对于追踪更奇怪的错误至关重要。
- 某些错误消息具有第二个组成部分，用于描述所涉及的内存地址。该图显示写入的内存刚好超过 example.c 第 5 行中使用 malloc() 分配的块的末尾。

接着，可以看到内存泄露的错误信息：

```sh
==19182== 40 bytes in 1 blocks are definitely lost in loss record 1 of 1
==19182==    at 0x1B8FF5CD: malloc (vg_replace_malloc.c:130)
==19182==    by 0x8048385: f (a.c:5)
==19182==    by 0x80483AB: main (a.c:11)
```

堆栈跟踪告诉你泄漏的内存是在哪里分配的（忽略 vg_replace_malloc.c ，这是一个实现细节）。

泄露有几种类型：

- "definitely lost"：你的代码一定有内存泄露，请修复它。
- "probably lost"：你的代码存在内存泄露，除非说你在使用指针做很有趣的事情。

Memcheck 也会报告未初始化值就被使用的错误：

- 最常见的是 "Conditional jump or move depends on uninitialised value(s)"，确定这些错误的根本原因可能很困难。
- 尝试使用 `--track-origins=yes` 来获取额外信息。这使得 Memcheck 运行速度变慢，但获得的额外信息通常可以节省大量时间来确定未初始化值的来源。

## 注意事项

Memcheck 并不完美：

- 它偶尔会误报，并且有机制可以抑制这些错误。但是 99% 都是正确的，因此你应该仅可能不要关闭和忽略这些错误。
- 它无法检测到程序中的每个内存错误。例如，它无法检测对静态分配或堆栈上分配的数组的超出范围读取或写入。但是它应该检测到许多可能导致程序崩溃的错误（例如导致分段错误）。

尝试使您的程序 Memcheck-clean，一旦达到这种状态，就可以更容易地看到程序的更改何时导致 Memcheck 报告新错误。
