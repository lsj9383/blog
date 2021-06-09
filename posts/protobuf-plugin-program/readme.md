# Protobuf Plugin Program

<!-- TOC -->

- [Protobuf Plugin Program](#protobuf-plugin-program)
    - [Overview](#overview)
    - [Quick Start](#quick-start)
    - [Compile Protoc Plugin](#compile-protoc-plugin)
    - [How To Use Plugin](#how-to-use-plugin)
    - [Bazel](#bazel)
    - [References](#references)

<!-- /TOC -->

## Overview

Protobuf 官方似乎并没有提供详细的插件编程入门指导和示例，因此要进行 Protobuf 插件编程是具有一定门槛的，例如：

- 插件的工作机制是怎么样的。
- 我们如何去编译插件代码。
- 我们如何在 protoc 运行时，指定运行我们的 protobuf 插件。
- 插件代码如何去解析 Protobuf 文件，Protobuf 为插件开发者提供了什么接口。

本文将带着这些问题，对 Protobuf 插件编程进行总结和梳理。

## Quick Start

在 Quick Start 中，我们提供一种 Python 脚本（其实任意语言都可以）的方式来进行 Protoc 的插件编译，因为采用 Python 脚本，因此并不需要我们编译插件，即写即用（但是需要安装 Protobuf 的 Python 依赖包）。

Protoc 在解析 `.proto` 文件后，会拉起 Plugin 子进程，并通过 stdin，将相关解析数据交给 Plugin 子进程进行处理。

- 首先，安装相关依赖：

  ```sh
  # Demo 中使用 virtualenv 生成解释器，使用 Python3.6
  $ virtualenv venv --python=python3.6
  $ source ./venv/bin/active

  # 安装 Python 对 Protobuf 插件编程的依赖
  $ pip install protobuf
  ```

- 接着，我们提供一个简单的 `.proto` 文件，请参考 [hello.proto](quic-start/hello.proto)。
- 我们提供 Python 脚本 [protoc-gen-custom](quic-start/protoc-gen-custom)。
- 最后，我们可以在 protoc 运行时指定插件进程（Python 插件脚本名叫 `protoc-gen-custom`，文件名没有 `.py` 后缀）：

  ```sh
  protoc --plugin=protoc-gen-custom=./protoc-gen-custom --custom_out=. hello.proto 
  ```

- 运行后，我们可以看到如下输出:

  ```sh
  $ protoc --plugin=protoc-gen-custom=./protoc-gen-custom --custom_out=. hello.proto 
  hello.proto
    Messages: 
      FooRequest
      FooResponse
      Hello
    Services: 
      Foo
  
  # 也生成了 proto.profile
  $ cat proto.profile
  hello.proto
    Messages: 
      FooRequest
      FooResponse
      Hello
    Services: 
      Foo
  ```

更多 protoc 使用插件的内容，请参考 [How To Use Plugin](#how-to-use-plugin)。

对于 CodeGeneratorRequest 和 CodeGeneratorResponse 所暴露的接口可以参考 [protobuf plugin.pb.h](https://developers.google.com/protocol-buffers/docs/reference/cpp/google.protobuf.compiler.plugin.pb?hl=ja)。

上述工作方式入下图所示：

![python-profile](assets/python-profile.png)

## Compile Protoc Plugin

## How To Use Plugin

将 Plugin 的二进制文件编译好后，需要在 protoc 编译时进行使用，有两种方式指定插件：

- 通过 `--plugin` 参数，指定插件二进制文件路径：

  ```sh
  # 以下 NAME 是插件的名称
  protoc --plugin=protoc-gen-NAME=path/to/mybinary --NAME_out=OUT_DIR
  # e.g. NAME = xrpc, PATH = /data/workspace/xrpc-plugin/xrpc_cpp_plugin
  protoc --plugin=protoc-gen-xrpc=/data/workspace/xrpc-plugin/xrpc_cpp_plugin --xrpc_out=OUT_DIR
  ```

- 将 Plugin 的二进制文件放置到环境变脸 PATH 的任意路径下，并且将二进制文件命名为 `protoc-gen-NAME` (NAME 是插件名称)，这样就不用通过 `--plugin` 参数指定使用的插件：

  ```sh
  protoc --NAME_out=OUT_DIR
  # e.g. NAME = xrpc
  protoc --xrpc_out=OUT_DIR
  ```

## Bazel

Bazel 是 Google 提供的编译工具，我们如何使用 Bazel 引入 Protobuf 插件进行编译呢？

## References

- [protobuf plugin.pb.h](https://developers.google.com/protocol-buffers/docs/reference/cpp/google.protobuf.compiler.plugin.pb?hl=ja)
- [protobuf plugin.h](https://developers.google.com/protocol-buffers/docs/reference/cpp/google.protobuf.compiler.plugin)
- [Protoc 及其插件工作原理分析(精华版)](https://www.hitzhangjie.pro/blog/2017-05-23-protoc%E5%8F%8A%E6%8F%92%E4%BB%B6%E5%B7%A5%E4%BD%9C%E5%8E%9F%E7%90%86%E5%88%86%E6%9E%90%E7%B2%BE%E5%8D%8E%E7%89%88/)
- [Protobuf 第三方扩展开发指南](https://www.jianshu.com/p/6f24de5f0f93)
- [通过 C++ 接口为 Protobuf 实现第三方扩展](https://www.jianshu.com/p/a9b93dea96ed)
- [Pod Plugin](https://github.com/snow1313113/pod_plugin)
- [A demo protoc plugin](https://github.com/vsco/protoc-demo)
