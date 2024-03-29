# 微服务应用的架构

[TOC]

## 概览

在实际微服务落地中，通常会将将微服务应用设计为四层结构：

- 平台层
- 服务层
- 边界层
- 客户端层

## 整体架构

软件设计师希望所开发出来的软件是易于修改的。

许多外部力量都会对开发者的软件施加影响：新增需求、系统缺陷、市场需要、新客户、业务增长情况等。

理想情况下，工程师可以自信满满地以稳定的步调来响应这些压力。如果想要做到这一点，开发方式就应该减少摩擦并将风险降至最低。

随着时间的不断推移，系统也在不断演进，工程团队想要：

- 将开发道路上的所有拦路石清理掉。
- 有的希望能够无缝地快速替换掉系统中过时的组件。
- 有的希望各个团队能够完全地实现自治，并各自负责系统的不同模块。
- 有的则希望这些团队之间不需要不停地同步各种信息而且相互没有阻碍。

为此，我们需要考虑一下架构设计，也就是构建微服务应用的规划。

### 从单体应用到微服务

在单体应用中，主要交付的就是一个应用程序。这个应用程序可以被水平地分成几个不同的技术层。

在典型的三层架构的应用中，它们分别是：

- 数据层
- 业务逻辑层
- 展示层

应用又会被垂直地分成不同的业务领域。MVC模式以及Rails和Django等框架都体现了三层模型。

![](assets/epub_31151874_59.jfif)

每一层都为其上一层提供服务：

- 数据层提供持久化状态
- 业务逻辑层执行有效操作
- 而展示层则将结果展示给终端用户

而对于微服务，其中单个微服务和单体应用是很相似的：

- 微服务会存储数据
- 执行一些业务逻辑操作
- 通过 API 将数据和结果返回给消费者

**每个微服务都具备一项业务能力或者技术能力**，并且会通过和其他微服务进行交互来执行某些任务。

单个服务的抽象架构如图：

![](assets/epub_31151874_60.jfif)

最重要的是，微服务并不是孤立地运行的。每个微服务都会和其他的微服务一起共存于一个环境中，而我们就在这个环境中开发、部署和运行微服务。应用架构应该包含整个环境。

### 架构师的角色

架构师或者技术负责人的工作就是要确保系统能够不断演进，而不是采用了固化的设计方案。

如果微服务应用是一座城市的话，开发者就是市政府的规划师。

架构师的职责是确保应用的技术基础能够支持快节奏的开发以及频繁的变化。

架构师应该具备纵观全局的能力，确保应用的全局需求都能得到满足，并进一步指导应用的演进发展：

- （1）应用和组织远大的战略目标是一致的。
- （2）团队共同承担一套通用的技术价值观和期望。
- （3）跨领域的内容——诸如可观察性、部署、服务间通信——应该满足不同团队的需要。
- （4）面对变化，整个应用是灵活可扩展的。

为了实现这些目标，架构师应该通过两种方式来指导开发：

- 第一，准则——为了实现更高一层的技术目标或者组织目标，团队要遵循的一套指南；
- 第二，概念模型——系统内部相互联系以及应用层面的模式的抽象模型。

### 架构准则

准则是指团队为了实现更高的目标而要遵循的一套指南（或规则）。准则用于指导团队如何实践。如下图所示：

![](assets/epub_31151874_62.jfif)

准则是灵活的，它们可以并且应该随着业务优先级的变化以及应用的技术演进而变化。

例如，早期的开发过程会将验证产品和市场需求的匹配度作为更高优先级的工作，而一个更加成熟的应用可能需要更专注于性能和可扩展性。

### 微服务应用的四层架构

这里提出了微服务应用的四层架构：

- （1）平台层——微服务平台提供了工具、基础架构和一些高级的基本部件，以支持微服务的快速开发、运行和部署。一个成熟的平台层会让技术人员把重心放在功能开发而非一些底层的工作上。
- （2）服务层——在这一层，开发的各个服务会借助下层的平台层的支持来相互作用，以提供业务和技术功能。
- （3）边界层——客户端会通过定义好的边界和应用进行交互。这个边界会暴露底层的各个功能，以满足外部消费者的需求。
- （4）客户端层——与微服务后端交互的客户端应用，如网站和移动应用。

![](assets/epub_31151874_63.jfif)

**注意：**

- 这里是对微服务应用的分层，而非对单个服务的分层。
- 单个服务就是三层。
- 微服务应用的每一层，都由多个微服务组成。

每一层都是建立在下一层次的功能之上的，比如，每个服务都会利用下层的微服务平台提供的部署流水线、基础设施和通信机制。要设计良好的微服务应用，需要在每个层级上都进行大量的投入并精心设计。

**注意：**

- 老实说，很多地方并不会认为基础设施需要单独起一层，一般会将基础设施认为是微服务应用依赖的外部系统之一。

## 微服务平台

微服务并不是独立存在的，微服务需要由如下基础设施提供支持：

- （1）服务运行的部署目标。包括基础设施的基本元件，如负载均衡器和虚拟机。
- （2）日志聚合和监控聚合用于观测服务运行情况。
- （3）一致且可重复的部署流水线，用于测试和发布新服务或者新版本。
- （4）支持安全运行，如网络控制、涉密信息管理和应用加固。
- （5）通信通道和服务发现方案，用于支持服务间交互。

如果把每个微服务看作一栋住宅，那么平台层提供了道路、自来水、电线和电话线：

![](assets/epub_31151874_64.jfif)

一个具有鲁棒性的平台层既能够降低整体的实现成本，又能够提升整体的可稳定性，甚至能提高服务的开发速度。

如果没有平台层，产品开发者就需要重复编写大量的底层的基础代码，无暇交付新的功能和业务价值。

在 AWS、Heroku 等 PaaS 平台上，已经提供了很多平台层能力，开发者在这一基础之上来开发微服务平台的其他部分。

在标准的云环境中运行微服务所需的部署配置：

![](assets/epub_31151874_65.jfif)

## 服务层

服务层，正如其名称所描述的——它就是服务所存在的地方。

在这一层，服务通过交互完成有用的功能：

- 服务层依赖于底层平台对可靠的运行和通信方案的抽象
- 服务层还会通过边界层将功能暴露给应用的客户端
- 我们同样还会考虑将服务内部的组件（如数据存储）也作为服务层的一部分

业务特点不同，相应服务层的结构也会差异很大。

### 功能

开发者所开发的服务实现的是不同的功能：

- （1）业务能力是组织为了创造价值和实现业务目标所做的工作。划到业务功能的微服务直接体现的是业务目标。
- （2）技术能力通过实现共享的技术功能来支持其他服务。

SimpleBank 的功能：

- order 服务公开了管理下单的功能——这是一个业务功能；
- market 服务是一个技术功能，它提供了和第三方系统通信的网关供其他服务。

![](assets/epub_31151874_66.jfif)

### 聚合与多元服务

在微服务应用的早期阶段，多个服务可能是扁平化的，每个服务的职责都是处于相似的层次的，比如：

- order 服务
- fee 服务
- transaction 服务
- account 服务

都处于大致相当的抽象水平。

随着应用的发展，开发者会面临服务增长的两大压力：

- 从多个服务聚合数据来为客户端的请求提供非规范化的数据（如同时返回费用和订单信息）。
- 利用底层的功能来提供专门的业务逻辑（如发布某种特定类型的订单）。这句话的意思使用微服务来提供专门的业务逻辑，满足特定的系统用例。

随着时间的推移，这两种压力会导致服务出现**层级结构的分化**：

- 靠近系统边界的服务会和某些服务交互以聚合它们的输出——我们将这种服务称为聚合器（aggregator）
- 除此之外，还有些专门的服务会作为协调器（coordinator）来协调下层多个服务的工作。

如下图所示：

![](assets/epub_31151874_68.jfif)

聚合器服务通过将底层服务的数据进行关联来实现查询服务，协调器服务会向下游服务发出各种命令来编配它们的行动

**注意：**

- 无论是聚合器，还是协调器，在软件方法中统一由 Control 实体映射。在很多地方也叫做应用层或编排层。

### 关键路径和非关键路径

随着系统的不断演进，有一些功能对顾客的需求和业务的成功经营来说越来越重要。

比如，在 SimpleBank 公司的下单流程中：

- order服务就处于关键路径。一旦这个服务运行出错，系统就不能执行客户的订单。
- 对应地，其他服务的重要性就弱一些。即便客户的资料服务不可用，它也不大会影响开发者提供的那些关键的、会带来收入的部分服务。

服务链对外提供功能，许多服务会参与到多个的路径中：

![](assets/epub_31151874_69.jfif)

微服务使得我们可以清楚地确定这些路径，然后对它们单独处理，投入更多的精力来尽可能提高这些关键路径的**可恢复性和可扩展性**，对于不那么重要的系统领域，则可以少付出一些精力。

## 通信

## 服务边界

边界层隐藏了内部服务的复杂交互，只展示了一个统一的外观。

像 Mobile App、网页用户界面或者物联网设备之类的客户端都可以和微服务应用进行交互。

### 边界层封装服务细节

边界层对内部的复杂度和变更进行了封装和抽象，如果没有边界层的话，客户端就需要对每个服务都了解很多信息，最后变得和系统的实现耦合越来越严重（比如，可以为列出所有历史订单的客户端提供一个固定不变的接口，但是在经过一段时间以后完全重构这个功能的内部实现）。

如下图，整个微服务应用为不同类型的客户端提供服务：

![](assets/epub_31151874_81.jfif)

为了避免客户端了解微服务应用内各种服务，我们提供边界层来对请求进行包装：

![](assets/epub_31151874_82.jfif)

### 边界层提供访问接口

边界层提供了访问数据和功能的方法，以便客户端可以使用适合自己的传输方式和内容类型来访问。

比如，服务之间相互通信采用的是gRPC的方式，而对外的边界层可以暴露一个 HTTP API 给外部消费者，这种方式更适合外部应用使用。

边界层还可以实现一些其他面向客户端的功能：

- 认证和授权——验证API客户端的身份和权限；
- 限流——对客户端的滥用进行防卫；
- 缓存——降低后端整体的负载；
- 日志和指标收集——可以对客户端的请求进行分析和监控。

把这些边缘功能放到边界层可以将关注点的划分更加清晰。没有边界层的话，后端服务就需要独立实现这些事务，这会增加它们的复杂度。

开发者同样可以在服务层中用边界来划分业务领域，比如，下单流程包括几个不同的服务，但是应该只有边界层服务会暴露出其他业务领域可以访问的切入点。

**注意：**

- 内部服务边界通常反应的是限界上下文：整个应用业务领域中关系比较紧密的有边界的业务子集。我们会在下一章探讨这部分内容。
- 因为限界上下文和子域之间最佳实践是一一映射，所以一般就是一个子域会有至少一个边界层服务。

边界服务存在于在微服务网应用的不同的限界上下文中：

![](assets/epub_31151874_84.jfif)

### API 网关作为边界层

通常而言，API 网关就是边界层。

API 网关在底层的服务后端之上为客户端提供了一个统一的入口点。它会代理发给下层服务的请求并对它们的返回结果进行一定的转换。

API 网关也可以处理一些客户端关注的其他横向问题，比如认证和请求签名。

![](assets/epub_31151874_86.jfif)

网关会对请求进行认证，如果认证通过，它就会将请求代理到对应的后端服务上。它还会对收到的结果进行转换，这样返回的数据更适合客户端。

从安全的角度来看，网关也能够将系统的暴露范围控制到最小。我们可以将内部的服务部署到一个专用网络中，限制除网关以外的所有请求进入。

**注意：**

- API 网关会执行 API 组合（composition）的工作：将多个服务的返回结果汇总到一个结果中。
- API 网关和服务层的聚合模式的界限很模糊。
- 最好注意一些，尽量避免将业务逻辑渗透到 API 网关中，这会极大增加网关和下层服务之间的耦合度。

### 服务于前端的后端（BFF）

BFE 是 API 网关的一种变形，尽管 API 网关模式很简洁，但是它也存在一些缺点：

> 如果 API 网关为多个客户端应用充当组合点的角色，它承担的职责就会越来越多。

假设开发者同时服务于`桌面应用`和`移动应用`：

- `桌面设备`通常具有较为稳定的网络环境，展示数据较多，可以支持复杂操作。
- `移动设备`通常网络环境不稳定，可用带宽低，展示数据少，用户功能也会有不同，如定位和环境识别。

在操作层面，这意味着`桌面 API`与`移动 API`的需求会出现分歧，因此开发者需要集成到网关的功能就会越来越宽泛。

不同的需求可能还会相互冲突，比如某个指定资源返回的数据量的多少（以及体积的大小）。在开发内聚的 API 和对 API 进行优化时，在这些相互竞争的因素间进行平衡是很困难的。

在BFF方案中，开发者会为每种客户端类型提供一个API网关。以SimpleBank公司为例，它们提供的每种服务都有一个自己的网关。

![](assets/epub_31151874_88.jfif)

### 消费者驱动网关

类似于 GraphQL，不太重要，略过。

## 客户端
