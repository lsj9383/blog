# CPU Profiler

[TOC]

## 概览

cpu-profiler 是 Google 会使用的 CPU 分析器。要使用 cpu-profiler 主要分为三个步骤：

1. 链接 profiler 库；
1. 运行代码；
1. 分析输出。

## 链接 Profiler

链接 Profiler 有两种方式：

链接方式 | 推荐 | 链接方法 | 程序运行方法
-|-|-|-
静态库链接 | √ | g++ -static -lprofiler -lunwind ... | 直接运行
动态库链接 |   | g++ -Bdynamic -lprofiler ... | 指定动态库路径：`env LD_PRELOAD="/usr/lib/libprofiler.so" <binary>`

将代码链接后，并不会真的开启 cpu 分析，还需要通过开关启动。

## 运行代码

运行代码时，启动 cpu-profiler 的方式有：

启动方式 | 描述 | 启动示例 | 备注
-|-|-|-
环境变量方式 | 将环境变量 CPUPROFILE 指定为需要 dump 的 profile 文件名即可启动。| env CPUPROFILE=ls.prof /bin/ls | 一个奇怪的问题，当我使用静态库方式链接后，不能使用环境变量方式启用 cpu-profiler。
信号方式 | 在指定 CPUPROFILE 的基础上，再为 CPUPROFILESIGNAL 指定为监听的信号，收到该信号开启 cpu-profiler（初始默认为关闭），并再次收到该信号时结束分析。| env CPUPROFILE=chrome.prof CPUPROFILESIGNAL=12 /bin/chrome &<br>开始分析：killall -12 chrome<br>结束分析（会生成 cpu-profile）：killall -12 chrome
代码控制 | 通过 ProfilerStart() 开启分析，并用 ProfilerStop() 结束分析。| 参考下面示例。

## 运行代码

对于环境变量方式，可以通过指定 CPUPROFILE 启动：

```sh
$ env CPUPROFILE=my.prof ./profiler_test

# 如果使用的是动态库，又缺乏动态库地址，可以指定 LD_PRELOAD
$ env LD_PRELOAD="/usr/local/lib/libprofiler.so" CPUPROFILE=my.prof ./profiler_test
```

对于代码控制的一个简单示例：

```cpp
#include <gperftools/profiler.h>

// "my.prof" 是 cpu-profiler 输出的分析文件名。
ProfilerStart("my.prof");
{
  // <code>
}
ProfilerStop();
// Stop 后会生成 cpu-profile 文件
```

**注意：**

- 比较奇怪的是，如果使用了静态库编译的方式，再用 CPUPROFILE 环境变量去启动，是无法启动 cpu-profiler 的。此时好像只能用代码方式。
- 对于代码方式，进程运行周期较长，可以中途进行 dump：`ProfilerFlush()`。

### 调整 CPUPROFILE 参数

环境变量 | 默认值 | 描述
-|-|-
CPUPROFILE_FREQUENCY | 100 | cpu-profiler 每秒采样多少个中断。有些运行较快的代码，可以提高采样频率，否则采用信息太少无法进行分析。
CPUPROFILE_REALTIME | 0 | 不重要，保持默认即可。具体可参考：[CPU profiler](https://gperftools.github.io/gperftools/cpuprofile.html)。

### 并发 Profile

gperftools 的 cpu-profiler 无法自适应于并发场景。这里的并发场景包括：

- 多进程并发。父进程启用 cpu-profiler 后，fork 出子进程。
- 多线程并发。使用 pthread_create 创建多线程。
- 多协程并发。
- ... 一切存在并发逻辑流的场景 ...

无论上述何种情况，都会分析输出到相同的文件，这会导致输出的文件内容混乱。

为了解决这个问题，强烈建议使用代码控制：

- 为每个并发逻辑单独进行 cpu-profiler。
- 以逻辑流的 ID（如进程 ID/线程 ID）作为文件名，进而将这些不同的逻辑流输出到不同的文件。

## 分析输出

gperftools cpu-filer 的输出文件名由 CPUPROFILE 指定，或者由代码中的 `ProfilerStart(<name>)` 参数指定。

### 文本输出

最简单的方式就是文本输出方式，能够快速且清晰的看到节点的调用情况（这里的节点指的是一个函数，也可以修改口径为文件）。

通过以下方式可以得到文本的输出：

```sh
# pprof <binary> <cpu-profile> --text
$ pprof profiler_test my.prof --text
...
14   2.1%  17.2%       58   8.7% std::_Rb_tree::find
```

文本输出的信息包括：

- 第一列：在该函数的采样数。
- 第二列：在该函数的采样数占所有采样的百分比。
- 第三列：不清楚，感觉不重要。
- 第四列：该函数，及它所调函数的采样累积。
- 第五列：第四列占总采样数的百分比。

### callgrind 输出

callgrind 是一种调用关系的输出方式。最简单的形式是生成 svg 文件：

```sh
# pprof <binary> <cpu-profile> --svg > myprof.svg
$ pprof profiler_test my.prof --svg > myprof.svg
```

生成的 callgrind 是一个带有调用信息和比例的关系图：

![](assets/pprof-test.gif)

每个节点，代表一个过程函数，节点的边代表的函数调用关系。每个节点的信息包括：

```txt
Class Name
Method Name
local(percentage)
of cumulative(percentage)
```

虽然这里节点显示的是采样次数，但是因为采样的频率是配置的，因此可以推出采样周期，进而得到节点所花的时间。

### 关注和忽略

为了减少旁支末节的信息，可以选择关注哪些采样，也可以选择忽略哪些采样：

- 关注：`ppof --gv --focus=vsnprintf /tmp/profiler2_unittest test.prof`
- 忽略：`pprof --gv --ignore=snprintf /tmp/profiler2_unittest test.prof`

除此外，还有更多的忽略方式：

选项 | 描述
-|-
--nodecount=n | This option controls the number of displayed nodes. The nodes are first sorted by decreasing cumulative count, and then only the top N nodes are kept. The default value is 80.
--nodefraction=f | This option provides another mechanism for discarding nodes from the display. If the cumulative count for a node is less than this option's value multiplied by the total count for the profile, the node is dropped. The default value is 0.005; i.e. nodes that account for less than half a percent of the total time are dropped. A node is dropped if either this condition is satisfied, or the --nodecount condition is satisfied.
--edgefraction=f | This option controls the number of displayed edges. First of all, an edge is dropped if either its source or destination node is dropped. Otherwise, the edge is dropped if the sample count along the edge is less than this option's value multiplied by the total count for the profile. The default value is 0.001; i.e., edges that account for less than 0.1% of the total time are dropped.
--focus=re | This option controls what region of the graph is displayed based on the regular expression supplied with the option. For any path in the callgraph, we check all nodes in the path against the supplied regular expression. If none of the nodes match, the path is dropped from the output.
--ignore=re | This option controls what region of the graph is displayed based on the regular expression supplied with the option. For any path in the callgraph, we check all nodes in the path against the supplied regular expression. If any of the nodes match, the path is dropped from the output.

### pprof 口径

我们的统计口径都是函数（例如上免的 callgrind 和文本输出都是以函数为节点），我们是可以修改该统计口径的：

pprof 参数 | 描述
-|-
--addresses | 每个程序地址生成一个节点。
--lines | 每条源代码行生成一个节点。
--functions | 每个函数生成一个节点（这是默认设置）。
--files | 每个源文件生成一个节点。

### 火焰图输出

## 参考文献

1. [CPU profiler](https://gperftools.github.io/gperftools/cpuprofile.html)
