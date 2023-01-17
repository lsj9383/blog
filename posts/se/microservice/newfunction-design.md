# 新功能设计

[TOC]

## 概述

我们需要探讨：

- 基于业务能力和使用用例划分微服务
- 按技术能力划分微服务的时机
- 服务边界不明确时的设计决策
- 多团队负责微服务场景下的有效范围划分

在微服务应用中设计新功能时，需要仔细而合理地划定微服务的范围。设计师需要决定何时开发一个新服务、何时扩展已有服务、如何划定服务之间的边界以及服务之间采用何种协作方式。

设计良好的服务有三大关键特性：

- 只负责单一职责
- 可独立部署
- 可替换

如果微服务的边界设计不合理或者粒度太小的话，这些微服务之间就会耦合得越来越紧，进而也就越来越难以独立部署和替换。紧耦合会增大变更的影响和风险：

- 如果服务太大（承担了太多职责功能的话）这些服务的内聚性就会变差，从而导致在开发过程中出现越来越多的摩擦。变更影响的调用方就会越多。
- 如果服务太小（没有承担单一职责），那么实现一个功能可能需要变更多个服务，发布、监控会变得更困难。 

即便一开始服务的大小是合适的，工程师也需要牢记：大多数复杂软件应用的需求都是会随着时间不断变化的，早期阶段可行的方案并不意味着永远都是合适的。没有哪种设计方案是永远完美的。

## 新功能

需要完成一个新功能，我们会分为四个阶段来完成设计：

1. 了解业务问题、用户案例和潜在的解决方案。
1. 确定服务所要支持的不同实体和业务功能。
1. 为负责这些功能的服务划定范围。
1. 根据当前和未来的潜在需求验证设计方案。

对此，通过以下示例来说明：

> 还记得SimpleBank公司吗？他们的团队做得非常棒——客户非常喜欢他们的产品！但是SimpleBank公司发现大部分客户并不想由他们自己来选择投资产品，而更愿意让SimpleBank公司来替他们做这份苦差事。那么我们研究一下，在微服务应用中找出一个解决这一问题的办法。

首先，我们了解一下需要解决的业务问题。在现实世界中，我们可以使用一些技巧来发现和分析业务问题，其中包括市场调研、客户访谈或者影响地图（impact mapping）。除了要了解的问题本身，我们还需要判断这是否是公司应该解决的问题。好在这不是一本关于产品管理的书——我们可以跳过这部分内容。

SimpleBank 公司目前的问题：

> SimpleBank 公司的客户需要自行选择如何利用自己的钱来进行投资，即便他们对投资一无所知。无知的投资者可能选择有高预期回报的资产，却没有意识到预期回报越高通常意味着风险也就越高。

SimpleBank 在业务上如何解决这个问题：

> SimpleBank 公司会让用户从许多预先制订好的多种投资策略（investment strategy）中选择一种，然后以客户的名义进行投资。投资策略取决于不同的资产类型（债券、股票、基金等的占比情况），这些资产的比例是根据风险水平和投资时间来设计的。客户向自己的账户充值以后， SimpleBank 会自动将这笔钱按照对应的策略来进行投资。

该过程通过下面用例图描述：

![](assets/epub_31151874_93.jfif)

我们可以确定出如下需要实现的用例：

1. SimpleBank公司必须能够创建和更新可选的策略；
1. 客户必须能够创建账户和选择适合的投资策略；
1. 客户必须能够采用一种策略进行投资，并且按照该策略投资能够正确生成对应的订单。

至此，我们在业务角度，找到了系统用例。

## 按业务能力划分

在明确了业务需求后，下一步就是确定技术解决方案：需要开发哪些功能，如何利用已有的微服务和要新开发的微服务来支持这些功能。

想要开发出成功的、可维护的微服务应用，为每个微服务**划定合适的范围**和**确定目标**是至关重要的。

这个过程被称作：

- 服务划界（service scoping）
- 它也被称作分解（decomposition）
- 或分区（partitioning）

一般由三种划分策略（三种策略并不冲突，通常融合使用）：

1. 按照业务能力和限界上下文（bounded context）划分。服务将对应于粒度相对粗一些但又紧密团结成一个整体的业务功能领域。
1. 按用例划分。这种服务应该是一个“动词”型，它反映了系统中将发生的动作。
1. 按易变性划分。服务会将那些未来可能发生变化的领域封装在内部。

### 能力和领域建模

业务能力是指组织为了创造价值和实现业务目标所做的事情，被划为业务能力一类的微服务直接反映的是业务目标。

因此，设计系统的组织结构时，将那些变化区域封装在内部是很自然的事情。

到目前为止，我们已经见过了一些通过服务所实现的业务能力：

- 订单管理
- 分类交易账簿
- 费用收取
- 向市场下单

微服务提供的功能及其与 SimpleBank 体现的业务能力的关系：

![](assets/epub_31151874_94.jfif)

一个领域的任何解决方案都是由若干个限界上下文组成的：

- 每个上下文内的各个模型是高度内聚的，并且对现实世界抱有相同的认知。
- 每个上下文之间都有明确且牢固的边界。

限界上下文是有着清晰范围和明确外部边界的内聚单元。这就使得它们很自然会成为服务范围划分的起点。在一套解决方案中的各个领域部分之间通过上下文相互划定界限。这种上下文边界通常和组织边界非常吻合。比如，电子商务公司在发货和顾客支付这两个领域上的需求并不相同，对应的开发团队也不同。

通常而言：

- 在开始的时候，一个限界上下文通常直接和一个服务以及一块业务能力领域相关联。
- 随着业务不断发展得越来越复杂，到最后，我们可能需要将一个上下文分解为多个子功能，其中的许多子功能需要实现为一个个独立的、相互协作的服务。
- 从客户端的角度看，这个上下文仍旧可以从逻辑上展示为一个服务。
- 每个上下文都进行微服务应用分层，例如每个上下文都需要有一个 API 网关。

### 创建投资策略

我们可以按照业务能力的划分方式来设计一些服务来提供创建投资策略的功能。为了让用例更加直观，我们用线框图画出了这个功能的界面原型。如下图所示：

![](assets/epub_31151874_97.jfif)

想要按照业务能力来设计服务的话，最好从一个领域模型开始。那什么是领域模型？

> 领域模型就是对限界上下文中业务所要执行的功能以及所涉及的实体的描述。

一个简单的投资策略包含两部分：名称和一组按百分比分配的资产。SimpleBank公司的管理员负责创建策略。

创建投资策略功能所需要的实体组成的领域模型：

![](assets/epub_31151874_98.jfif)

这些实体的设计模型图会有助读者理解服务所要拥有和保存的数据。另外，我们至少已经确定了两个新的服务：用户管理（user management）和资产信息（asset information）。用户（user）和资产（asset）实体分别属于截然不同的两个限界上下文:

1. 用户管理——它包括诸如注册、认证和授权这样的功能。在银行环境中，出于安全、法规和隐私方面的原因，为不同的资源和功能授权是受到严格管制的。
1. 资产信息——它包括与第三方市场数据提供方服务的集成，这些数据包括资产价格、类别、等级以及财务业绩等。另外，还包括用户界面上所要求的资产搜索功能。

我们可以将策略和客户账户关联起来，然后用它们来生成订单。账户和订单是两个截然不同的限界上下文，但是投资策略既不属于账户上下文，也不属于订单上下文：

- 当策略发生变化时，这个变化并不会影响账户和订单它们自己的功能。
- 反过来，将投资策略添加到账户或者订单中任何一个服务中都会阻碍相应服务的可替代性，降低服务的内聚性，增大修改的难度。

这些因素表明投资策略是一种独立的业务能力，我们需要一个新的服务。

上下文与现有功能的关系如图：

![](assets/epub_31151874_99.jfif)

首先，投资策略服务需要暴露创建和获取投资策略的方法。这样，其他服务或管理后台界面就可以访问这个数据了。

我们还应该考虑一下这个服务应该发出什么事件消息。基于事件的模型有助于解除服务之间的耦合，这可以确保我们能编排耗时较长的服务交互，而不需要显式地编配出这些交互过程。

投资策略微服务的内外通信契约：

![](assets/epub_31151874_102.jfif)

我们已经确定了这个用例所有需要支持的功能。为了了解这些功能是如何相互配合的，我们可以将investment strategy服务与其他在线框图中已经明确的功能进行关联：

![](assets/epub_31151874_103.jfif)

我们总结一下目前所做的工作：

- 针对示例问题，确定了业务创造价值所要完成的功能以及 SimpleBank 公司不同的业务领域范围之间固有的边界；
- 借助这些知识，识别出属于不同能力的实体和职责，确定了**微服务应用**的边界（微服务应用会进一步分层拆分）；
- 将系统划分到一个个能够反映这些业务领域边界的服务中。

通过这种方法设计出来的服务相对稳定、有内聚性、面向业务价值并且相互之间耦合度低。

### 内嵌性上下文和服务

每个限界上下文都会为其他上下文提供API，同时将内部操作封装起来。我们以资产信息为例研究一下：

![](assets/epub_31151874_104.jfif)

这种私有操作和对外接口分开的方案提供了为服务演化提供了一种非常有用的途径：

- 在系统生命周期的前期，我们可以选择开发粒度粗一些的服务来体现高层次的边界。
- 随着时间的推移，我们可能在未来需要将服务分解，将内部嵌套的上下文中的功能开放出来。

这样就能够保持服务的可代替性以及高内聚性，即使业务逻辑的复杂度越来越高。

### 挑战和不足

## 按用例划分

## 按易变划分

## 处理不确定性

## 组织中的服务所有权