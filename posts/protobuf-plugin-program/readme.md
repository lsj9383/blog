# Protobuf Plugin Program

<!-- TOC -->

- [Protobuf Plugin Program](#protobuf-plugin-program)
    - [Overview](#overview)
    - [Quick Start](#quick-start)
    - [How to use plugin](#how-to-use-plugin)
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

**注意：**

- 本文主体针对 C++ 开发 Protobuf 插件。
- 为了更容易阐述 Protobuf 插件开发的核心思想，在 [Quick Start](#quick-start) 中提供了 Python 语言进行开发的示例。

## Quick Start

protoc 在解析 `.proto` 文件后，会拉起 Plugin 子进程，并通过 stdin，将相关解析数据交给 Plugin 子进程进行处理。

首先，安装相关依赖：

```sh
# Demo 中使用 virtualenv 生成解释器，使用 Python3.6
$ virtualenv venv --python=python3.6

# 安装 Python 对 Protobuf 插件编程的依赖
$ pip install protobuf
```

接着，我们提供一个简单的 `.proto` 文件：

```proto
// hello.proto

syntax = "proto3";

service Foo {
  rpc Bar(FooRequest) returns(FooResponse);
}

message FooRequest {
  string content = 1;
}

message FooResponse {
  string content = 1;
}

message Hello {
  string name = 1;
}
```

我们期望输出一个文件，包含 `.proto` 文件的概览。我们提供这样的 Python 脚本：

```py
#!/data/workspace/proto/venv/bin/python

import sys

from google.protobuf.compiler import plugin_pb2 as plugin
from google.protobuf.descriptor_pb2 import DescriptorProto, EnumDescriptorProto


def generate_code(request, response):
    parts = []
    for f in request.proto_file:
        parts.append(f.name + "\n")
        parts.append("  Messages: \n")
        for m in f.message_type:
            parts.append("    " + m.name + "\n")
        parts.append("  Services: \n")
        for s in f.service:
            parts.append("    " + s.name + "\n")
    content = "".join(parts)

    # 打印调试信息, 因为标准输出是给 protoc 父进程获取用的，因此这里使用标准错误输出进行打印
    sys.stderr.write(content)

    # 生成文件和内容
    response.file.add()
    response.file[0].name = 'proto.profile'
    response.file[0].content = content


if __name__ == '__main__':
    # 从标准输入中获取二进制数据，并解析成 CodeGeneratorRequest 结构
    data = sys.stdin.buffer.read()
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(data)

    # 构建 CodeGeneratorResponse，用于设置响应
    response = plugin.CodeGeneratorResponse()
    generate_code(request, response)

    # 序列化 CodeGeneratorResponse，通过标准输出返回给 protoc 父进程。
    output = response.SerializeToString()
    sys.stdout.buffer.write(output)
```

**注意：**

- 第一行必须是解释器的名称，否则无法有效的启动 Python 进程。Demo 中提供的是由 virtualenv 生成的 Python 解释器。

最后，我们可以在 protoc 运行时指定插件进程（Python 插件脚本名叫 `protoc-gen-custom`，文件名没有 `.py` 后缀）：

```sh
protoc --plugin=protoc-gen-custom=/data/workspace/proto/custom/protoc-gen-custom --custom_out=. hello.proto 
```

运行后，我们可以看到如下输出:

```sh
$ protoc --plugin=protoc-gen-custom=/data/workspace/proto/custom/protoc-gen-custom --custom_out=. hello.proto 
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

更多 protoc 使用插件的内容，请参考 [How to use plugin](#how-to-use-plugin)。

上述工作方式入下图所示：

![python-profile](assets/python-profile.png)

## How to use plugin

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

Bazel 是 Google 提供的编译工具，我们如何在 Bazel 中进行 Protobuf 插件的生成和使用呢？

## References

- [protobuf plugin.h](https://developers.google.com/protocol-buffers/docs/reference/cpp/google.protobuf.compiler.plugin)
- [Protoc 及其插件工作原理分析(精华版)](https://www.hitzhangjie.pro/blog/2017-05-23-protoc%E5%8F%8A%E6%8F%92%E4%BB%B6%E5%B7%A5%E4%BD%9C%E5%8E%9F%E7%90%86%E5%88%86%E6%9E%90%E7%B2%BE%E5%8D%8E%E7%89%88/)
- [Protobuf 第三方扩展开发指南](https://www.jianshu.com/p/6f24de5f0f93)
- [通过 C++ 接口为 Protobuf 实现第三方扩展](https://www.jianshu.com/p/a9b93dea96ed)
- [Pod Plugin](https://github.com/snow1313113/pod_plugin)
- [A demo protoc plugin](https://github.com/vsco/protoc-demo)
