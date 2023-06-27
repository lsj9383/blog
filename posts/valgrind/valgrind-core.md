# 使用和理解 Valgrind

[TOC]

## 概述

主要介绍 Valgrind 的核心功能，通用选项和行为，因此无论使用 Valgrind 的什么工具，都和本文相关。这些信息应该足以让您有效地日常使用 Valgrind。

> 本文主要参考 [Using and understanding the Valgrind core](https://valgrind.org/docs/manual/manual-core.html)。

## Valgrind 对你的程序做了什么

Valgrind 尽可能的设计成无侵入性的工具，它可以直接与可执行文件一起使用：

```sh
# 你的程序原本运行方式
$ your-prog [your-prog-options]

# 使用 valgrind 后的程序运行方式
$ valgrind [valgrind-options] your-prog [your-prog-options]
```

最重要的 Valgrind 选项是 `--tools`，它指定了使用哪个工具，进行什么样的调试和分析：

```sh
$ valgrind --tool=memcheck ls -l

# 默认的 Valgrind 工具就是 memcheck，因此在这个场景下其实无需指定 memcheck 工具
$ valgrind ls -l
```

**注意：**

- 无论使用哪种工具，Valgrind 都会在程序启动之前控制您的程序。
- 调试信息是从可执行文件和关联的库中读取的，以便在适当的时候可以根据源代码位置来表达错误消息和其他输出。


Valgrind 可能会探测出系统库中的错误，通常而言，这些错误你不会感兴趣，因为通常是你无法修改的。因此 Valgrind 可以读取你事先编写好的抑制文件，来选择性的抑制错误。

为了更方便的编写抑制文件，可以使用 `-gen-suppressions=yes` 选项，它能告诉 Valgrind 在遇到每个错误信息时，提供相应的抑制文件编写方式，然后将这个文本复制到抑制文件中。

## 评论（The Commentary）

Valgrind 工具将会撰写评论，这是一个文本流，详细说明错误报告和其他重要事件。注释中的所有行都具有以下形式：

```txt
==12345== some-message-from-Valgrind
```

**注意：**

- 这里 12345 是进程 ID。

这种方案可以很容易地区分程序输出和 Valgrind 注释，也很容易区分来自不同进程的注释（无论出于何种原因，这些进程已经合并在一起运行被 Valgrind 分析了）。

你可以将你的 Valgrind 评论输出到三个不同的地方：

1. 输出到 stderr（默认，文件描述符为 2），可以通过使用 `--log-fd=9` 的形式，将输出流转移到其他文件描述符。
1. 输出到指定文件，可以通过 `--log-file=filename` 指定。
1. 发送到网络 Socket。这里不展开。

## 报告错误

## 抑制错误

抑制文件并不容易编写，到目前为止，最简单的抑制编写方式：

- 使用 ` --gen-suppressions=yes` 选项，它会为每个错误生成一个抑制的文本。

每个抑制文件有如下几个部分：

- 首行：提供抑制的名称，该名称并不重要，旨在进行标识。在 Valgrind -v 会使用通过该名称告知用户进行了什么抑制。
- 次行：抑制文件使用到哪个 Valgrind 工具上（多个工具，则以逗号分隔），以及进行什么抑制。例如：`tool_name1,tool_name2:suppression_name`。
- 下一行：少数抑制类型在第二行之后有额外信息（例如Param Memcheck 的抑制）
- 剩余行：这是错误的调用上下文——导致错误的函数调用链。这些行最多可以有 24 条。

一个抑制文件示例：

```supp
# demo.supp
{
   demo_supp
   Memcheck:Addr4
   fun:f
   fun:main
}
```

使用抑制文件：

```sh
valgrind --suppressions=demo.supp ./ac
```

如果需要知道使用了哪些抑制：

```sh
$ valgrind --suppressions=demo.supp -v ./ac
# ...
# ...
--31156-- 
--31156-- used_suppression:      1 memcheck_addr4_demo demo.supp:2
# ...
```

## 核心命令选项

Valgrind 的选项分为两部分：

- 核心命令选项，即所有 Valgrind 工具共用的命令项。
- 工具命令选项，即特定于工具使用的命令项。

对于核心命令选项，在大多数情况下，Valgrind 的默认设置成功地给出了合理的行为。这里主要介绍**核心命令选项**。

### 工具选项

选项 | 默认值 | 描述
-|-|-
`--tool=<toolname>` | memcheck | 指定运行的 Valgrind 工具，例如：memcheck, cachegrind, callgrind, helgrind, drd, massif, dhat, lackey, none, exp-bbv 等。
`--trace-children=<yes|no>` | no | 取值为 yes 时，将会跟踪通过 exec 启动的子进程。这是多进程程序跟踪时的必要选项。**注意：** 对于 Fork 的子进程，valgrind 是自动跟踪的（很难不做到自动跟踪，因为 Fork 会拷贝整个进程空间）。

### 基本选项

选项 | 默认值 | 描述
-|-|-
-h --help | - | 
--help-debug |

## 调用数

在 Windows 环境下可以使用 [QCacheGrind]()
