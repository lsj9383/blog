# Bazel 编译 Protoc 插件

```sh
# 编译 protoc-gen-demo
$ bazel build :protoc-gen-demo
INFO: Analyzed target //plugin:protoc-gen-demo (0 packages loaded, 0 targets configured).
INFO: Found 1 target...
Target //plugin:protoc-gen-demo up-to-date:
  bazel-bin/plugin/protoc-gen-demo
INFO: Elapsed time: 0.063s, Critical Path: 0.00s
INFO: 1 process: 1 internal.
INFO: Build completed successfully, 1 total action

# 处理 proto 文件
$ protoc --plugin=protoc-gen-demo=bazel-bin/protoc-gen-demo --demo_out=. hello.proto 
--custom_out: hello.proto: ========= IT IS A TEST ========
```
