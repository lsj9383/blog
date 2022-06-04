# Avoid Flags, Especially in Library Code

Quicklink:

- [目录](../readme.md)
- [原文链接](https://abseil.io/tips/45)

在生产代码（尤其是库中），通常不应该使用标识（Flags）：除非确实有必要，否则不要使用标识。

标识是一个**全局变量**，更糟糕的是，你不能通过阅读代码知道该标识的取值，因为标识不仅可以在启动时设置，也会后续任何时刻被改变。
