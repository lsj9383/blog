# XRPC Thread Model

<!-- TOC -->

- [XRPC Thread Model](#xrpc-thread-model)
    - [Overview](#overview)
    - [Quick Start](#quick-start)
    - [Structure](#structure)
    - [Sequence Diagram](#sequence-diagram)
        - [Initial Sequence Diagram](#initial-sequence-diagram)
        - [Handle Thread Run Sequence Diagram](#handle-thread-run-sequence-diagram)
        - [IO Thread Run Sequence Diagram](#io-thread-run-sequence-diagram)
        - [Handle Thread Task Sequence Diagram](#handle-thread-task-sequence-diagram)
        - [IO Thread Task Sequence Diagram](#io-thread-task-sequence-diagram)
    - [Thread Model Initial](#thread-model-initial)
        - [Server Initial](#server-initial)
        - [Client Initial](#client-initial)
    - [Task](#task)
    - [ThreadModel](#threadmodel)
    - [ThreadModelManager](#threadmodelmanager)
        - [Defualt Thread Model](#defualt-thread-model)
    - [Options](#options)
        - [ThreadModel::Options](#threadmodeloptions)
        - [WorkerThreadImpl::Options](#workerthreadimploptions)
        - [DefaultIoModelImpl::Options](#defaultiomodelimploptions)

<!-- /TOC -->

## Overview

XRPC 框架支持的线程模型是很多的，但是由于种种原因，这里仅分析了 XRPC 的异步线程模型。

一个 XRPC 应用中可以使用多个不同类型的线程模型，每个类型的线程模型又可以初始化多个实例，但通常而言，我们只需要确定使用的线程模型类型，以及一个对应的线程模型实例即可。

线程模型的类型有三种：

- default，异步回调的线程模型，可以结合 [future](future.md) 使用。
- fiber，协程模型，本文不会提及。
- spp，另一种协程模型，本文不会提及。

defualt 线程模型又分为两种处理方式：

- seperate，IO 线程和 Handle 线程分离，IO 线程处理网络事件，Handle 线程处理具体的业务。
- merge，IO 线程和 Handle 线程合并，每个线程都能处理网络事件和业务的线程。

## Quick Start

Default 线程模型本质上就是一个线程池，通过一个提交 Task 至线程模型的 Demo，可以直观的了解到 XRPC 线程池交互方式。

线程模型配置：

```yaml
global:
  local_ip: 127.0.0.1
  threadmodel:
    default:
      - instance_name: default_instance
        io_handle_type: seperate
        io_thread_num: 8
        handle_thread_num: 10
```

提交一个 Task 到线程模型中运行：

```c++
// 通过线程模型的类型和名称获得线程模型
// std::string threadmodel_type = "default";                       // default 是默认线程模型
// std::string threadmodel_instance_name = "default_instance";     // default_instance 是线程模型的名字，线程模型的名字在 yaml 文件的 global 中定义
// auto thread_model = ThreadModelManager::GetInstance()->GetThreadModel("default", "default_instance");
auto thread_model = xrpc::ThreadModelManager::GetInstance()->GetDefaultThreadModel();

// 构建一个任务
xrpc::Task* task = new xrpc::Task();
task->group_id = thread_model->GetThreadModelId();      // 线程模型 ID
task->task_type = TaskType::TRANSPORT_REQUEST;          // 任务的类型
task->dst_thread_key = -1;                              // 随机选择一个 Worker 执行 Task
task->handler = [](Task* task) mutable {
    std::cout << "hello world" << std::endl;
};

xrpc::TaskResult result = thread_model->SubmitHandleTask(task);
```

提交一个 Period Timer Task 到线程模型中运行：

```c++
auto thread_model = xrpc::ThreadModelManager::GetInstance()->GetDefaultThreadModel();
xrpc::Task* task = new xrpc::Task;
task->group_id = thread_model->GetThreadModelId();
task->task_type = xrpc::TaskType::TRANSPORT_REQUEST;
task->handler = [=](xrpc::Task* task) {
    xrpc::TimerTaskInfo* timer_task_info = new xrpc::TimerTaskInfo();
    timer_task_info->cancel = false;
    timer_task_info->expiration = xrpc::TimeProvider::GetNowMs() + 1000;
    timer_task_info->interval = 5000;     // ms
    timer_task_info->executor = [=]() {
        auto tid = std::this_thread::get_id();
        std::cout << "tid:" << tid << std::endl;
    };

    xrpc::Task* timer_task = new xrpc::Task;
    timer_task->group_id = thread_model->GetThreadModelId();
    timer_task->task_type = xrpc::TaskType::TIMER;
    timer_task->task = reinterpret_cast<void*>(timer_task_info);
    timer_task->handler = nullptr;
    thread_model->SubmitTimerTask(timer_task);
};

// 用 Thread Model Task 包装 Timer Task
// 这是因为 xrpc 框架要求提交 Timer Task 的线程必须属于 XRPC Thread Model 的线程
thread_model->SubmitHandleTask(task);
```

## Structure

线程模型中涉及到的对象是非常多的，XRPC 对线程模型进行了层层抽象与封装。

XRPC Thread Model 涉及到如下对象：

- ThreadModelManager，线程模型管理器，可以拥有多个 ThreadModel。
- ThreadModel，线程模型，一个线程模型管理了一个线程池，线程池中的对象是 WorkThread。
- WorkThread，对线程的抽象，该对象并不实际负责处理逻辑，而是交由 WorkThradImpl 完成处理逻辑。
  - WorkThradImpl，负责线程的初始化、启动、销毁等逻辑，对任务的处理交由 io_model 或 handle_model 完成。
- HandleModel，Handle 线程处理对象，负责定时任务、队列任务的循环处理。
- IoModel，IO 线程处理对象，除了对定时任务、队列中任务进行处理外，还负责重要的调度 Reactor 处理网络事件。

```mermaid
classDiagram

    class ThreadModelManger {
    }

    class ThreadModel {
    }

    class WorkerThread {
    }

    class WorkerThreadImpl {
    }
```

## Sequence Diagram

### Initial Sequence Diagram

这里展示了 ThreadModelManager 如何对 ThreadModel 及相关对象初始化的流程：

```mermaid
sequenceDiagram
autonumber

participant thread_model_manager as ThreadModel Manager
participant thread_model as ThreadModel
participant work_thread_impl as WorkThreadImpl
participant io_model as IO Model
participant handle_model as Handle Model

loop 循环创建线程模型 ThreadModel

    thread_model_manager ->> thread_model_manager: 初始化线程模型 ID，设置 options.threadmodel_id

    loop 根据配置的线程个数, 循环创建线程 WorkThread
        alt IO 线程
            thread_model_manager ->> thread_model_manager: 构造 IO Model Impl
            thread_model_manager ->> thread_model_manager: 构造 IO Model
        else Handle 线程
            thread_model_manager ->> thread_model_manager: 构造 Handle Model Impl
            thread_model_manager ->> thread_model_manager: 构造 Handle Model
        end
        thread_model_manager ->> thread_model_manager: 构造 Task Queue

        thread_model_manager ->> work_thread_impl: 实例化 WorkThread
        work_thread_impl -->> thread_model_manager: 返回 WorkThread 实例
        thread_model_manager ->> thread_model_manager: 将 WorkThread 添加至 options.worker_threads
    end

    thread_model_manager ->> thread_model: 传递 options 以实例化 ThreadModel
    thread_model ->> thread_model: 保存 options
    thread_model ->> thread_model: 通过传递过来的线程池，进一步拆分用于 IO 的线程池和 Handle 的线程池并保存
    thread_model -->> thread_model_manager: 返回 ThreadModel 实例
end

loop 循环初始化 ThreadModel
    thread_model_manager ->> thread_model: 初始化 ThreadModel
    loop 循环初始化 WorkThread
        thread_model ->> work_thread_impl: 通知进行初始化
        alt 线程属于 IO 线程
            work_thread_impl ->> io_model: 通知初始化
            io_model -->> work_thread_impl: 初始化完成
        else 线程属于 Handle 线程
            work_thread_impl ->> handle_model: 通知初始化
            handle_model -->> work_thread_impl: 初始化完成
        end
        work_thread_impl -->> thread_model: 初始化完成
    end
    thread_model -->> thread_model_manager: 初始化完成

    thread_model_manager ->> thread_model: Start ThreadModel
    loop 循环启动 WorkThread
        thread_model ->> work_thread_impl: 启动线程
        work_thread_impl ->> work_thread_impl: 启动线程，线程中会区分 io_model 和 handle_model 使用不同的逻辑
        work_thread_impl -->> thread_model: 启动完成
    end
    thread_model -->> thread_model_manager: 启动完成

end
```

在 WorkThreadImpl 中实现了线程的启动，对于 IO 类型的线程和 Handle 类型的线程处理方式是不同的：

```cpp
void WorkerThreadImpl::Run() {
  // 信号处理注册 ...

  // 核绑定 ...

  // 替换线程的名字 ...

  if (options_.role == WorkerThread::Role::IO ||
      options_.role == WorkerThread::Role::IO_HANDLE) {
    options_.io_model->Run();
  } else {
    options_.handle_model->Run();
  }
}
```

### Handle Thread Run Sequence Diagram

Handle 线程是 Seperate 模式的工作线程，主要是：

- 心跳上报（若配置开启）
- 处理任务

```mermaid
sequenceDiagram
autonumber

participant work_thread_impl as WorkThreadImpl
participant io_model as IO Model
participant handle_model as Handle Model
participant handle_impl as Default Handle Impl
participant task_queue as Task Queue

work_thread_impl ->> work_thread_impl: 线程启动

work_thread_impl ->> work_thread_impl: 信号设置

work_thread_impl ->> work_thread_impl: 绑核

work_thread_impl ->> work_thread_impl: 设置线程名字

alt 属于 Handle 线程
work_thread_impl ->> handle_model: Run

alt 开启了 RPC 心跳上报
    work_thread_impl ->> work_thread_impl: 心跳上报配置初始化
end
handle_model ->> handle_impl: Run

loop !terminate_

handle_impl ->> handle_impl: 检查是否满足心跳上报的条件，若满足则进行心跳上报
handle_impl ->> handle_impl: 任务队列为空，等待 10 ms
handle_impl ->> handle_impl: 获得超时任务
loop 遍历超时任务
    handle_impl ->> handle_impl: 执行超时任务
end

loop 遍历 Task
    handle_impl ->> task_queue: 获取 Task
    task_queue -->> handle_impl: 返回 Task
    handle_impl ->> handle_impl: 执行任务
end

end

handle_impl -->> handle_model: 线程退出

handle_model -->> work_thread_impl: 线程退出
end
```

### IO Thread Run Sequence Diagram

IO 线程存在于 Seperate 和 Merge 两种工作模式中，其运行时序图如下所示：

```mermaid
sequenceDiagram
autonumber

participant work_thread_impl as WorkThreadImpl
participant io_model as IO Model
participant io_model_impl as IO Model Impl
participant reactor as Reactor
participant poller as Epoll Poller
participant task_queue as Task Queue

work_thread_impl ->> work_thread_impl: 线程启动

work_thread_impl ->> work_thread_impl: 信号设置

work_thread_impl ->> work_thread_impl: 绑核

work_thread_impl ->> work_thread_impl: 设置线程名字

alt 属于 IO 线程
    work_thread_impl ->> io_model: Run
    io_model ->> io_model_impl: Run

    alt 开启了 RPC 心跳上报
        io_model_impl ->> io_model_impl: 心跳上报配置初始化
    end
    io_model_impl ->> reactor: Run

    loop !terminate_
        reactor ->> poller: Dispatch(timeout=5ms)
        poller ->> poller: 使用 epoll wait 等待事件（网络事件、定时器事件）
        poller ->> poller: 处理所有事件
        poller -->> reactor: 处理完成

        reactor ->> task_queue: 获取任务队列
        task_queue -->> reactor: 返回任务队列
        reactor ->> reactor: 遍历所有任务执行
    end

    reactor ->> task_queue: 获取任务队列
    task_queue -->> reactor: 返回任务队列
    reactor ->> reactor: 遍历所有任务执行

    reactor -->> io_model_impl: 线程退出
    io_model_impl -->> io_model: 线程退出
    io_model -->> work_thread_impl: 线程退出
end
```

### Handle Thread Task Sequence Diagram

这里显示 Handle Thread 处理任务以及定时器任务的时序图。

为了简化时序图的复杂度，这里我省略掉了一些代理对象，心跳逻辑，仅展示核心流程。

```mermaid
sequenceDiagram
autonumber

participant user as User
participant thread_model as ThreadModel
participant task_timer as Task Timer
participant task_queue as Task Queue
participant handle_impl as Default Handle Impl

par Handle Thread 逻辑
    handle_impl ->> handle_impl: 线程运行

    loop !terminate_
        handle_impl ->> task_timer: 获得超时任务
        task_timer ->> task_timer: 遍历所有任务，将超时的任务都返回
        task_timer -->> handle_impl: 返回超时任务集合
        handle_impl ->> handle_impl: 遍历执行超时任务

        handle_impl ->> task_queue: 获取 Task
        task_queue -->> handle_impl: 返回 Task
        handle_impl ->> handle_impl: 遍历执行任务
    end
and User 逻辑
    user ->> user: 从 ThreadModelManager 中获得需要的 ThreadModel

    user ->> user: 构造任务 Task，包括 Task 的 handler、指定运行 task 的线程等
    user ->> thread_model: SubmitHandleTask
    thread_model ->> thread_model: 判断 task.group_id 是否属于当前 ThreadModel 的 ID
    thread_model ->> thread_model: 通过 task.dst_thread_key 选择运行 Task 的线程队列，队列和 Worker 是绑定的
    alt 若运行 Task 的线程为 User 所处线程
        thread_model ->> thread_model: 直接调用 task.handler
    else 若运行 Task 的线程不为 User 线程
        thread_model ->> task_queue: 向指定线程的队列分发 task
        task_queue -->> thread_model: 分发完成
    end
    thread_model -->> user: 提交任务完成

    user ->> user: 构造 Timer Task
    user ->> thread_model: SubmitTimerTask
    alt User 线程不属于 ThreadModel
        thread_model ->> thread_model: 进程放弃处理, core
    end
    thread_model ->> task_timer: CreateTimer 创建定时器任务
    task_timer -->> thread_model: 定时器任务创建完成
    thread_model -->> user: 提交定时任务完成
end
```

User 通过和 ThreadModel 交互可以将 Task 交给 Handle Impl，那 User 如何获取 ThreadModel 呢？使用 `GetThreadModel` 或 `GetDefaultThreadModel` 即可：

```cpp
auto thread_model = ThreadModelManager::GetInstance()->GetThreadModel("default", "default_instance");
// 等价于
auto thread_model = ThreadModelManager::GetInstance()->GetDefaultThreadModel();
```

细节请参考 [ThreadModelManager](#threadmodelmanager)。

### IO Thread Task Sequence Diagram

IO 线程处理方式和 Handle 处理方式的差别是巨大的，原因是：

- IO Thread 除了处理普通 Task 外，还需要处理网络相关的任务
- IO Thread 需要处理网络事件
- IO Thread 的 Timer Task 使用 Epoll + Timer FD 的方式实现（Handle Thread 的 Timer Task 使用定期检查的方式实现）

对于 IO 线程的网络事件处理更详细的内容，请参考 [Network Model](../xrpc-network-model/readme.md)。

```mermaid
sequenceDiagram
autonumber


```

## Thread Model Initial

从上面时序图我们已经可以看到线程模型整个流程，那么线程模型是什么时候初始化的，进而推动 XRPC 线程运作的呢？

虽然 XRPC Server 和 XRPC Client 的 Thread Model 初始化触发方式是不一样的，但是其本质都是一致的：通过 XRPC Plugin 进行初始化。

```cpp
int XrpcPlugin::RegistryPlugins() {

  InitCompress_();

  InitSerialization_();

  // ===========================================================
  // ================= INITIAL Thread Model ====================
  // ===========================================================
  InitThreadModel_();

  InitCodec_();

  InitNaming_();

  InitConfig_();

  InitMetrics_();

  InitLogging_();

  InitSsl_();

  InitAuth_();

  InitFilters_();

  InitStreamHandler_();

  return 0;
}

int XrpcPlugin::InitThreadModel_() {
  // ===========================================================
  // ================= INITIAL Thread Model ====================
  // ===========================================================
  int ret = ThreadModelManager::GetInstance()->Init();

  assert(ret == 0);

  return 0;
}
```

但是 XRPC Server 和 Client 触发 Plugin 的 RegisterPlugins 方法的时机是不一样的。

### Server Initial

XRPC Server 在 Server 的启动时就会自动调用 RegisterPlugins。

```cpp
int main() {
  // app is XrpcApp
  app.Main(argc, argv);
  app.Wait();
}

void XrpcApp::Wait() {
  InitializeRuntime();

  // blocking in this function
  DestoryRuntime();

  DestoryFrameworkRuntime();
  TimeProvider::Destory();
}

void XrpcApp::InitializeRuntime() {
  // ...
  InitPlugins();
  // ...

  server_->Start();
}

void XrpcApp::InitPlugins() { XrpcPlugin::GetInstance()->RegistryPlugins(); }
```

### Client Initial

XRPC Client 分两种情况讨论：

- 由 XRPC Server 中运行的 Client，因为 XRPC Server 初始化时已经初始化 Thread Model 了，所以这种情况下不用额外再作任何初始化。
- 纯 XRPC Client，需要手动触发。

```cpp
int main(int argc, char *argv[]) {
  // Initial...

  // 获取客户端配置
  xrpc::ClientConfig client_config = xrpc::XrpcConfig::GetInstance()->GetClientConfig();

  // 创建客户端对象
  xrpc::XrpcClient client(client_config);

  // =======================================
  // 初始化插件，这里会触发 ThreadModel 的初始化
  // =======================================
  xrpc::XrpcPlugin::GetInstance()->RegistryPlugins();

  // do something

  //  注销插件
  xrpc::XrpcPlugin::GetInstance()->UnregistryPlugins();
}
```

## Task

线程池使用任务进行驱动，这里是对任务的定义：

```cpp
// 任务类型
using TaskHandler = std::function<void(Task*)>;

enum class TaskType {
  FINISH,                       // 结束任务，这是一个特殊的任务，用于通知线程池结束
  TRANSPORT_REQUEST,            // 网络请求任务
  TRANSPORT_RESPONSE,           // 网络响应任务
  TIMER,                        // 定时器任务
};

struct Task {
  TaskType task_type;           // 任务类型

  void* task;                   // 和 Task 绑定的上下文指针，便于 Task 执行时获取上下文信息

  TaskHandler handler;          // Task 的执行 Handler, TaskHandler = std::function<void(Task*)>;

  int group_id;                 // 线程模型 ID

  int dst_thread_key = -1;      // 分发 Task 到哪个线程中运行，这个是线程的索引（并非线程 ID），-1 则随机分发。
};
```

## ThreadModel

## ThreadModelManager

### Defualt Thread Model

## Options

XRPC 中存在非常多的配置，这里将 Thread Model 涉及到的 Options 进行梳理。

需要注意的，下面所有的 Options，均是在 ThreadModelManager 中进行初始化和设置的，直接传递给相关的对象进行使用。

### ThreadModel::Options

`ThreadModel::Options` 是 ThreadModel 的配置，主要是告知 ThreadModel 其模型 ID，以及线程池。

```cpp
class ThreadModel {
 public:
  struct Options {
    uint16_t threadmodel_id;                                        // 当前线程模型实例的唯一id
    std::vector<std::unique_ptr<WorkerThread>> worker_threads;      // 线程集合
  };
};
```

### WorkerThreadImpl::Options

`WorkerThreadImpl::Options` 是线程的工作配置，最重要的是指定了其线程类型，以及实际执行的逻辑的 io_model 和 handle_model。

```cpp
class WorkerThread {
 public:
  // 线程角色
  enum class Role {
    IO = 0x01,
    HANDLE = 0x10,
    IO_HANDLE = 0x11,
  };
};

class WorkerThreadImpl : public WorkerThread {
 public:
  struct Options {
    // 当前工作线程的工作角色，决定使用 IO 线程还是 Handle 线程处理
    WorkerThread::Role role;

    // 当前工作线程的逻辑 id，在 ThreadModelManager 进行相关线程初始化的时候设置
    // id = ((threadmodel_id << 16) + i);
    uint32_t id;

    // IO 线程处理对象
    std::unique_ptr<IoModel> io_model;

    // Handle 线程处理对象
    std::unique_ptr<HandleModel> handle_model;
  };
};
```

### DefaultIoModelImpl::Options

`DefaultIoModelImpl::Options` 是 IO Model 的配置，最重要的是其包装的 Reactor，这是 IO 线程进行网络操作的核心对象。

```cpp
class DefaultIoModelImpl : public IoModelImplBase {
 public:
  struct Options {
    // 每个 iomodel会 在具体线程模型里的某一个工作线程运行
    // 因此，此逻辑 id 需要与其绑定的工作线程 id 一致
    uint32_t id;

    // 所属线程模型的instance_name
    std::string instance_name;

    // iomodel默认采用reactor模型实现
    std::unique_ptr<Reactor> reactor;
  };
};
```
