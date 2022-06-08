# Abseil：C++ Tips of the Week 翻译

<!-- TOC -->

- [Abseil：C++ Tips of the Week 翻译](#abseilc-tips-of-the-week-翻译)
    - [概览](#概览)
    - [C++ Tips of Week 翻译目录](#c-tips-of-week-翻译目录)
    - [参考文献](#参考文献)

<!-- /TOC -->

## 概览

什么是 Abseil？Abseil 是一个 C++ 库的开源集合，并广泛应用于 Google 的各个项目中。参考官网的解释：

> Abseil is an open source collection of C++ libraries drawn from the most fundamental pieces of Google’s internal codebase. These libraries are the nuts-and-bolts that underpin almost everything Google runs.

更多详情可以参考 [About Abseil](https://abseil.io/about/)。

Google 内部发布了一系列 C++ 技巧，大约每周一次，被称为 C++ Tips of Week（TotW），并在 Google 内部成为经典，被大量引用。

Google 通过 Abseil 开发社区公布这些 TotW，本文的即是对这些 TotW 的翻译，旨在学习和记录。

需要注意的是，Google 所公布的 TotW 的序号并非是顺序的，这是因为保留了原本内部 Google 的引用序号，读者不必深究。

> We will be keeping the original numbering scheme on these tips, and original publication date, so that the 12K or so people that have some exposure to the original numbering don't have to learn new citations. As a result, some tips may appear missing and/or out of order to a casual reader. But rest assured, we're giving you the good stuff.

## C++ Tips of Week 翻译目录

- [TotW #1: string_view](totw1/readme.md)
- [TotW #3: String Concatenation and operator+ vs. StrCat()](totw3/readme.md)
- [TotW #5: Disappearing Act](totw5/readme.md)
- [TotW #10: Splitting Strings, not Hairs](totw10/readme.md)
- [TotW #11: Return Policy](totw11/readme.md)
- [TotW #24: Copies Abbrv](totw24/readme.md)
- [TotW #36: New Join API](totw36/readme.md)
- [TotW #42: Prefer Factory Functions to Initializer Methods](totw42/readme.md)
- [TotW #45: Avoid Flags, Especially in Library Code](totw45/readme.md)
- [TotW #49: Argument-Dependent Lookup](totw49/readme.md)
- [TotW #55: Name Counting and unique_ptr](totw55/readme.md)
- [TotW #61: Default Member Initializers](totw61/readme.md)
- [TotW #64: Raw String Literals](totw64/readme.md)
- [TotW #65: Putting Things in their Place](totw65/readme.md)
- [TotW #74: Delegating and Inheriting Constructors](totw74/readme.md)
- [TotW #77: Temporaries, Moves, and Copies](totw77/readme.md)
- [TotW #86: Enumerating with Class](totw86/readme.md)
- [TotW #88: Initialization: =, (), and {}](totw88/readme.md)

## 参考文献

1. [About Abseil](https://abseil.io/about/)
1. [C++ Tips of the Week](https://abseil.io/tips/)
1. [C++ Tips of the Week 中文翻译](https://github.com/tianyapiaozi/TotW)
