# Valgrind

[TOC]

## 概述

Valgrind 是什么？

> Valgrind is an instrumentation framework for building dynamic analysis tools.

也就是说，Valgrind 是一个用于进行程序动态分析的框架。

Valgrind 提供了多种多样的工具，每个工具都能进行某种调试、分析或类似的任务。

同时，Valgrind 是模块化的，因此可以很方便的进行插件式扩展。

Valgrind 提供了非常多的标准工具：

工具 | 描述
-|-
Memcheck | 这是一个内存错误的检测器，可以帮助你编写更好的 C/C++ 程序。
Cachegrind | 这是一个缓存和分支预测器，可以帮助你编写运行更快的程序。
Callgrind | 这是一个调用图分析器。
Helgrind | 这是一个线程错误检测器，帮助您使您的多线程程序更加正确。
DRD | 这也线程错误检测器。它与 Helgrind 类似，但使用不同的分析技术，因此可能会发现不同的问题。
Massif | 这是一个堆分析器，可以帮助你减少内存使用。
DHAT | 这是一个不同类型的堆分析器，它可以帮助您了解块寿命、块利用率和布局效率低下的问题。
BBV | 这是一个实验性的 SimPoint 基本块向量生成器。对于从事计算机体系结构研究和开发的人来说很有用。

## 目录

- [Valgrind 快速开始](quick-start.md)
- [使用和理解 Valgrind](valgrind-core.md)
