# Open Tracing


<!-- TOC -->

- [Open Tracing](#open-tracing)
    - [Overview](#overview)
    - [Specification](#specification)
    - [Python Demo](#python-demo)
        - [Jaeger](#jaeger)
        - [Sources](#sources)
    - [References](#references)

<!-- /TOC -->
## Overview

## Specification

## Python Demo

### Jaeger

OpenTracing 并没有限制使用 Tracing Server，但最常见的是 Jaeger。在其他一切开始前，我们先使用 Docker 在机器上运行 Jaeger：

```cpp
docker run \
  --rm \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 16686:16686 \
  jaegertracing/all-in-one:1.7 \
  --log-level=debug
```

Jaeger 运行起来后可以直接通过 IP:Port 的方式进行访问：

```text
http://9.134.9.104:16686/search
```

![jaeger-home.png](assets/jaeger-home.png)

### Sources

提供了三个层面的 Python OpenTracing 入门 Demo：

- [python-demo/hello.py]()
- [python-demo/hello-relationships.py]()
- [python-demo/hello-rpc.py]()

## References

1. [OpenTracing 中文文档](https://wu-sheng.gitbooks.io/opentracing-io/content/)
1. [The OpenTracing Semantic Specification](https://opentracing.io/specification/)
1. [OpenTracing Python](https://opentracing.io/guides/python/)
1. [Jaeger Getting Started](https://www.jaegertracing.io/docs/1.22/getting-started/)
1. [OpenTracing Tutorials](https://github.com/yurishkuro/opentracing-tutorial)
