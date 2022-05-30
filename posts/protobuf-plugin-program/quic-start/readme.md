# Quic Start

这是一个 Python 编写 Protoc 插件的 Demo：

```sh
# Demo 中使用 virtualenv 生成解释器，使用 Python3.6
$ virtualenv venv --python=python3.6
$ source ./venv/bin/active

# 安装 Python 对 Protobuf 插件编程的依赖
$ pip install protobuf

$ protoc --plugin=protoc-gen-custom=./protoc-gen-custom --custom_out=. hello.proto
hello.proto
  Messages: 
    FooRequest
    FooResponse
    Hello
  Services: 
    Foo
```

Python 插件使用了 [plugin.pb.h](https://developers.google.com/protocol-buffers/docs/reference/cpp/google.protobuf.compiler.plugin.pb?hl=ja) 所提供的接口。
