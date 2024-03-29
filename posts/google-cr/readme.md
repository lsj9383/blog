# Google Code Review 指南

[TOC]

## 概览

首先，什么是 Code Review（CR） ？

> A code review is a process where someone other than the author(s) of a piece of code examines that code.

CR 是代码作者以外的其他人，对代码进行检查的过程。

其次，CR 的意义是什么呢？CR 可以维护代码和产品的质量。

> At Google, we use code review to maintain the quality of our code and products.

那么，CR 到底应该检查什么？

检查项 | 中文 | 描述
-|-|-
Design | 设计 | 代码是否精心设计，并适合该系统。
Functionality | 功能 | 代码的行为是否符合作者的预期？该行为是否对用户有利。
Complexity | 复杂性 | 代码是否能够更简单？其他开发者是否易理解，并在此基础上使用和扩展。
Tests | 测试 | 代码是否具有设计良好的自动化测试。
Naming | 命名 | 是否为类、变量、函数等选择了清晰的名称。
Comments | 注释 | 注释是否清晰且有用？
Style | 风格 | 是否符合[代码规范](https://google.github.io/styleguide/)？
Documentation | 文档 | 是否更新了相关文档。

在 Google 的 CR 中有一些 “黑话”：

- CL，代表了 `changelist`，意思是已经提交给 git 或者处于代码审查的一个独立变更。等同于 change、patch、pull-request。
- LGTM，代表了 `Looks Good to Me`，即**我觉得不错**，代码审查人通过一个 CL 时会如此说。

既然要进行 CR，那谁是你的最佳评审者？

> The best reviewer is the person who will be able to give you the most thorough and correct review for the piece of code you are writing.

能够为你的代码变更进行完整、正确的审核的人就是最佳的 Reviewer。这通常意味着 Reviewer 就是代码的所有者。

因为仓库中的代码可能由多个人所有，因此某些时候会要求不同的人来 Review 不同 changelist 部分。

如果你的 Reviewer 现在无法进行 CR，至少应该抄送他们。

## 代码评审者：Code Review 标准

## 代码评审者：Code Review 需要做什么

在考虑这些审查要点时，务必遵循 Code Review 标准。

### 设计

CR 最重要需要覆盖的就是 changelist 的整体设计。例如：

- CL 中的这些代码块的交互是否有意义？
- CL 是否与系统的其他部分很好的集成在一起？
- 现在是添加此 CL 的好时机么？

### 功能性

功能性分两方面：

- 开发者的意图对用户是否有好处？
- CL 是否真的符合开发者的意图？

上面的**用户**一次，有两个维度：

- 最终用户，即受变更影响的涉众。
- 将来会使用、扩展这段代码的开发人员。

通常而言，开发人员需要对 CL 进行足够好的测试后，才应该提交 CR。作为评审者，仍然需要考虑各类边缘情况，寻找并发编程问题，确保代码在读起来没有 BUG。

如果需要，你可以体验 CL：对评审者而言，最重要的事情是检查 CL 对用户的影响，例如 UI 更改。当只是阅读代码时，可能很难感受到如何影响用户，此时可以让开发人员演示该功能并自己尝试。

另一个需要在 CR 时特别考虑的是并发编程，因为仅通过运行代码很难确保没有引入问题。

### 复杂性

CL 是否比其应该的更复杂？

**太复杂**，意味着`代码阅读者无法快速理解代码`，同时也意味着`开发人员在调用或修改代码时可能引入错误`。

一种特殊的复杂性是**过度工厂（over-engineering）**，开发人员使代码比它所需要的更通用，或者添加了系统目前不需要的功能。

> Encourage developers to solve the problem they know needs to be solved now, not the problem that the developer speculates might need to be solved in the future.

### 测试

### 命名

开发人员是否为所有的东西，选择了一个好的命名。

一个好的命名需要能够表达清楚**是什么**或**做什么**，但是也不应该太长以至于很难阅读。

> Did the developer pick good names for everything? A good name is long enough to fully communicate what the item is or does, without being so long that it becomes hard to read.

### 注释

开发者编写的英文注释是否足够清晰？注释是否必要？

通常而言，注释解释代码**为什么**存在很有用。但如果代码不能清晰的解释自己，那么应该让代码更简单。

多数注释是代码本身不可能包含的信息，例如决策背后的推理。

### 风格

在 Google 确保 CL 遵循了 [风格指南](https://google.github.io/styleguide/)。

### 一致性（Consistency）

### 文档

如果 CL 涉及到了用户的构建、测试、交互、发布，那么需要检查是否更新了相关文档（例如 README、自动生成的文档等）。

如果 CL 删除了废弃的代码，考虑是否文档中需要进行相应的删除。

如果文档忘记变更，则要求开发人员进行调整。

### 每一行

通常而言，评审者需要仔细看 CL 中的 **每一行**。一些时候，CL 中包括了数据文件、生成的代码或者大的数据结构体，对于此类可以快速扫一眼。

对于人工编写的类、方法、代码块需要仔细看，并且不能假设他们是可以好好工作的。显然，有些代码并另一些代码更值得仔细检查，这是评审者需要做出的判断，但无论如何，评审者应该理解所有的代码在干些什么。

如果对你来说阅读代码太难，并且这将减缓你的评审速度，你应该让开发人员知道，并让他们做出澄清后，再尝试评审。

如果你理解代码，但你认为自己没有资格对其中某一部分进行评审，则需要确保存在一个合格的评审者，能够对这部分进行评审，特别是对于隐私、安全、并发、可访问性、国际化等复杂问题。

你作为 CL 的评审者一员，你可能不需要评审每一行代码：

- 仅查看某些文件。
- 仅审查 CL 的某些方面，例如安全、隐私、高级设计等。

在这些情况下，请在评论中注明你查看了哪些部分，并尝试给与 LGTM 的评论。

### 上下文

### 鼓励

如果你在 changelist 中看到一个不错的变更，告诉开发者，尤其是当他们以出色的方式解决你的评论时。

CR 通常只关注错误，但它们也应该对良好实践进行鼓励和赞赏。

在指导方面，告诉开发者他们做对了什么比告诉他们做错了什么更有价值。

### 结论

在进行 CR 时，你应该做好以下的事情：

- 代码经过精心设计。
- 功能对于代码的用户而言是有利的。
- 任何对于 UI 的变更都是合理的，且看起来不错。
- 任何并发编程都是安全的。
- 代码足够简化。
- 开发者没有实现将来可能需要，但是现在不需要的事情。
- 代码有单元测试。
- 测试经过精心设计。
- 开发者使用了清晰的命名。能够解释**是什么**或**做什么**。
- 注释是清晰且有用的，注释解释**为什么**。
- 代码有适当的文档记录。
- 代码符合我们的风格指南。

## 代码评审者：快速 Code Review

## 代码作者：编写好的 CL 描述

## 代码作者：小型 CL

我们一次变更尽可能是一个小的 CL，而不是一个庞大的 CL。

### 为什么要小型 CL？

小型 CL 有以下优点：

优点 | 描述
-|-
评审更快 | 评审者一次花五分钟进行一个 CL 的评审，比留出 30min 进行一个大的 CL 评审更简单。
评审更彻底 | 大的变更，会导致评审者更难彻底的进行评审，甚至漏掉某些重要的点。
更少的 BUG 引入 | 由于做的变更足够小，你以及评审者都能有效的判断是否引入错误。
如果拒绝，浪费更小 | 如果你写了一个巨大的 CL，然后你的评审者说大方向是错误的，那你就浪费了很多工作。
更容易合并 | 处理大型 CL 需要很长时间，因此在合并时会遇到很多冲突。
更容易设计好 | 一个小改动的设计，比一个大改动的设计要简单得多。
减少评审所带来的阻塞 | 提交一个整体变更中的一小部分，可以让你在等待 CR 时，继续编程。
回滚更简单 | -

### 如何判断什么才是一个小的 CL？

通常而言，一个 CL 正确大小应该是一个独立的变更，这意味着：

- CL 只做了一个最小的变更，解决了一件事情。通常这个 CL 只是一个特性的一部分，而不是一个完整的特性。尽可能编写小的 CL，即便小到不合理，也比编写大的 CL 要好。你可以和你的评审者一起找到可接受的 CL 大小。
- CL 应该包含相关的测试代码。
- CL 评审者需要了解的关于 CL 的所有内容都在 CL、CL 描述、代码库、已经评审过的 CL 中。
- 当 CL 合并后，该系统能够继续为其用户正常工作。
- CL 不会小到其含义难以理解。如果你添加一个新的 API，你应该在 CL 中包含 API 的用法，以便评审者更好的了解 API 的使用方式。

关于**太大**并没有一个定量的规定，一个经验来看，主要是两方面：

- 变更行数。100 行左右是一个 CL 较为合理的大小，1000 行通常就太大了。
- 牵涉的文件数量。一个文件中 200 行的变更可能是没有问题的，但若分布在 50 个文件中，通常就太大了。

请记住，评审者可能并没有代码的上下文，而代码作者却始终和代码紧密相关，因此对于代码作者而言的 CL 合理大小，可能对于评审者而言就太大了。请编写小的 CL，评审者一般不会抱怨 CL 太小。

小型 CL 指的是一个集中的概念，而不是和行数有密切相关性的。

> Remember that smallness here refers the conceptual idea that the CL should be focused and is not a simplistic function on line count.

### 什么时候可以大型 CL？

但是我们也绝非完全不采用大型 CL，在某些情况下，大的 CL 并没有那么糟糕：

- 你可以将删除整个文件，视为一行变更，因为评审者不会花很多实践时间去审阅这个。
- 有时，你完全信任的自动重构工具会生成一个大型的 CL，而评审者的工作是确认要做这个变更。

### 分离重构

通常最好将重构、BUG 修复、特性开发的 CL 进行分离，而不是放入同一个 CL 中。

### 相关测试代码保存在同一个 CL 中

CL 应该包含相关的测试代码。

添加或更改逻辑的 CL 应该伴随新行为的测试，或更新的行为的测试。纯重构 CL，也应该进行测试。理想情况下，这些测试已经存在，但如果不存在，您应该添加它们。

### 不要破坏构建

如果你有多个相互依赖的 CL，您需要找到一个方法来确保每个 CL 提交后整个系统可以继续工作。

否则，您可能会在您提交 CL 之间的几分钟内中断所有开发人员的构建（如果您后来的 CL 提交出现意外问题，则可能会更长时间）。

### 无法让 CL 足够小

有时候，你的 CL 无法变小，这很少发生。经过小型 CL 编写练习的开发人员，总能将一个 CL 拆开一系列小的 CL。

如果真的无法让 CL 足够小，请提前通知你的评审者，让他们知道即将发生大型 CL 的 CR。

## 参考文献

1. [Google 工程实践](https://google.github.io/eng-practices/)
1. [Code Review Developer Guide](https://google.github.io/eng-practices/review/)
1. [The CL author’s guide to getting through code review](https://google.github.io/eng-practices/review/developer/)