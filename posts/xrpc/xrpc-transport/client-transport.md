# Xrpc Client Transport

<!-- TOC -->

- [Xrpc Client Transport](#xrpc-client-transport)
    - [Overview](#overview)
    - [Quick Start](#quick-start)
    - [UML Class Diagram](#uml-class-diagram)
    - [Sequence Diagram](#sequence-diagram)
        - [Submit Send Task](#submit-send-task)
        - [Send Task](#send-task)
        - [Get Response](#get-response)
    - [Client Transport](#client-transport)
        - [FutureTransport Initial](#futuretransport-initial)
        - [Async Send Impl](#async-send-impl)
        - [Sync Send Impl](#sync-send-impl)
        - [SendOnly](#sendonly)
        - [Backup Request](#backup-request)
    - [TransportAdapter](#transportadapter)
    - [ConnectorManager](#connectormanager)
    - [Connector](#connector)
        - [ConnPoolConnector](#connpoolconnector)
        - [ConnComplexConnector](#conncomplexconnector)
    - [FutureConnectionHandler](#futureconnectionhandler)
    - [IO Handler](#io-handler)
    - [TransportMessage](#transportmessage)
    - [Options](#options)
        - [FutureTransport::Options](#futuretransportoptions)
        - [TransInfo](#transinfo)

<!-- /TOC -->

## Overview

Client Transport 封装了 Xrpc Network Model 实现了更方便的、易于扩展的接口，包括：

- 用户可以自定义响应包检测函数
- 用户可以自定义响应包反序列化函数
- 用户可以自定义响应处理的线程
- 封装了 Promise Future 接口，方便接收和处理响应
- 封装了连接复用和连接池两种调用方式
- 封装了请求上下文，接收响应时可以正确获取发送时的上下文

## Quick Start

通过使用 Client Transport 的接口构造 HTTP 请求 Demo，来了解 Client Transport 如何使用：

```cpp
#include <iostream>
#include <memory>
#include <string>
#include <thread>

#include "xrpc/client/xrpc_client.h"
#include "xrpc/runtime/iomodel/reactor/default/default_connection.h"
#include "xrpc/runtime/iomodel/reactor/default/tcp_connection.h"
#include "xrpc/common/config/xrpc_config.h"
#include "xrpc/common/future/future_utility.h"
#include "xrpc/common/xrpc_plugin.h"
#include "xrpc/codec/xrpc/xrpc_protocol.h"
#include "xrpc/transport/client/future/future_transport.h"

void Test() {
  // 构造请求
  std::string message;
  message += "GET /ok HTTP/1.1\r\n";
  message += "Host: localhost\r\n\r\n";

  xrpc::STransportReqMsg request_message;
  request_message.basic_info = xrpc::object_pool::GetRefCounted<xrpc::BasicInfo>();
  request_message.basic_info->addr.ip = "127.0.0.1";
  request_message.basic_info->addr.port = 80;
  request_message.basic_info->addr.addr_type = xrpc::NodeAddr::AddrType::IP_V4;
  request_message.basic_info->timeout = 1000;  // ms
  request_message.send_data = xrpc::CreateBufferSlow(message.c_str(), message.size());;
  request_message.extend_info = new xrpc::ExtendInfo();

  // 网络事件回调
  auto thread_model = xrpc::ThreadModelManager::GetInstance()->GetDefaultThreadModel();
  xrpc::TransInfo trans_info;
  trans_info.checker_function = [=](const xrpc::ConnectionPtr& conn,
                                    xrpc::NoncontiguousBuffer& in,
                                    std::deque<std::any>& out) {
    // 检查数据包是否接收，默认接收到的数据是完整的，直接返回
    std::cout << "1. Check Function" << std::endl;
    out.push_back(in);
    in.Clear();
    return xrpc::PacketChecker::PACKET_FULL;
  };
  trans_info.rsp_decode_function = [=](std::any&& in, xrpc::ProtocolPtr& out) {
    // 将接收到的数据格式化，将响应存放在 直接返回 true
    std::cout << "2. Rsp Decode Function" << std::endl;
    out = std::make_shared<xrpc::XrpcResponseProtocol>();
    auto buf = std::any_cast<xrpc::NoncontiguousBuffer&&>(in);
    out->SetNonContiguousProtocolBody(std::move(buf));
    return true;
  };
  trans_info.rsp_dispatch_function = [=](xrpc::Task* task) {
    // 分发处理 Task 的方法
    std::cout << "3. Rsp Dispatch Function" << std::endl;
    task->group_id = thread_model->GetThreadModelId();
    thread_model->SubmitHandleTask(task);
  };
  trans_info.conn_type = xrpc::ConnectionType::TCP_LONG;
  trans_info.connection_idle_timeout = 50000;               // ms
  trans_info.is_complex_conn = false;                       // 使用连接池方式 默认
  trans_info.max_conn_num = 2;                              // Xrpc 默认用的是 64 个

  // 构造 Transport
  xrpc::FutureTransport::Options future_transport_option;
  future_transport_option.thread_model = thread_model;
  future_transport_option.trans_info = trans_info;
  xrpc::FutureTransport transport;
  transport.Init(future_transport_option);

  // 发起请求
  transport.AsyncSendRecv(&request_message).Then([=](xrpc::Future<xrpc::STransportRspMsg>&& fut) {
    if (!fut.is_ready()) {
    }

    auto response_message = std::get<0>(fut.GetValue());
    auto protocol = std::any_cast<xrpc::ProtocolPtr>(response_message.msg);
    auto res = dynamic_cast<xrpc::XrpcResponseProtocol*>(protocol.get());
    std::cout << "response data: " << std::endl << xrpc::FlattenSlow(res->GetNonContiguousProtocolBody()) << std::endl;

    return xrpc::MakeReadyFuture<>();
  }).Wait();
}

int main() {
  xrpc::XrpcConfig::GetInstance()->Init("test_transport_client.yaml");
  xrpc::XrpcPlugin::GetInstance()->InitThreadModel();
  Test();
  xrpc::XrpcPlugin::GetInstance()->DestroyThreadModel();
}
```

编译完成后可以使用该进程发请求：

```cpp
$ ./bazel-bin/test/test/test_transport_client
1. Check Function
2. Rsp Decode Function
3. Rsp Dispatch Function
response data: 
HTTP/1.1 200 OK
Server: openresty/1.13.6.2
Date: Sat, 15 May 2021 14:01:11 GMT
Content-Type: text/plain
Content-Length: 2
Connection: keep-alive

ok
```

## UML Class Diagram

```mermaid
classDiagram

ClientTransport <|-- FutureTransport
FutureTransportOptions <-- FutureTransport
FutureTransport --> TransportAdapter
TransportAdapterOptions <-- TransportAdapter

TransportAdapter --> ConnectorManager
ConnectorManagerOptions <-- ConnectorManager

ConnectorManager --> Connector
ConnectorOptions <-- Connector

Connector <|-- ConnPoolConnector
Connector <|-- ConnComplexConnector

ConnPoolConnector --> ConnPool

ConnPool --> DefaultConnection
ConnComplexConnector --> DefaultConnection

class ClientTransport {
  +Name()
  +Type()
  +Init(params) int
  +Start()
  +Stop()
  +Destory()
  +AsyncSendRecv(STransportReqMsg) Future_STransportRspMsg
  +SendRecv(STransportReqMsg, STransportRspMsg) int
  +SendOnly(STransportReqMsg) int
  +CreateStream(STransportReqMsg, StreamOptions)
}

class FutureTransport {
  +vector<TransportAdapter*> trans_adapters_
  +FutureTransportOptions options_
  +Name()
  +Version() string
  +Init(params) int
  +Start()
  +Stop()
  +Destory()
  +Roll(io_thread_num) uint16_t
  +SelectIOThread(io_thread_num)
  +AsyncSendRecv(STransportReqMsg) Future_STransportRspMsg
  +SendRecv(STransportReqMsg, STransportRspMsg) int
  +SendOnly(STransportReqMsg) int
}

class FutureTransportOptions {
  +ThreadModel* thread_model
  +TransInfo trans_info
  +string transport_name
}

class TransportAdapter {
  +TransportAdapterOptions options_
  +ConnectorManager connector_mgr_
  +GetConnector(STransportReqMsg) Connector
}

class TransportAdapterOptions {
  +IoModel io_model
  +TransInfo trans_info
}

class ConnectorManager {
  +ConnectorManagerOptions options_
  +map<std::string, Connector*> endpointId_to_connector_
  +ConnectorManager(STransportReqMsg) Connector
  +Destory() int
}

class ConnectorManagerOptions {
  +IoModel io_model
  +TransInfo trans_info
}

class Connector {
  +ConnectorOptions options_
  +uint64_t kConnectInterval
  +size_t pending_queue_size_limit_
  +size_t send_queue_size_limit_
  +TimeoutQueue send_req_timeout_queue_
  +TimeoutQueue pending_req_timeout_queue_
  +vector<uint32_t> timer_index_vec_
  +SendReqMsg(STransportReqMsg) int
  +SendOnly(STransportReqMsg) int
  +NotifySendMsgFunction(conn)
  +MessageHandleFunction(conn, rsp_list)
  +ConnectionCleanFunction(conn)
  +CreateTcpConnection(conn_id)
  +CreateUdpTransceiver(conn_id)
  +ActiveTimeUpdate(conn)
  +Destory() int
  +PushToSendReqTimeoutQueue(STransportReqMsg)
  +PopSendTimeoutQueue(request_id) STransportReqMsg
  +PushToPendingTimeoutQueue(STransportReqMsg)
  +PopPendingSendTask(STransportReqMsg) bool
  +DispatchResponse(STransportReqMsg, STransportRspMsg)
  +DispatchException(STransportReqMsg, ret, err_msg)

}

class ConnectorOptions {
  +IoModel* io_model
  +TransInfo* trans_info;
  +NetworkAddress peer_addr;
}

class ConnPoolConnector {
  +ConnPool conn_pool_
  +Destory() int
  +SendReqMsg(STransportReqMsg) int
  +MessageHandleFunction(conn, rsp_list) bool
  +ActiveTimeUpdate(conn)
  +NotifySendMsgFunction(conn)
  +ConnectionCleanFunction(conn)
  +CreateConnection(conn_id) DefaultConnection
  +GetConnection(STransportReqMsg) DefaultConnection
  +SetReqTimeoutHandler()
  +RemoveIdleConnection()
}

class ConnComplexConnector {
  +SendReqMsg(STransportReqMsg) int
  +MessageHandleFunction(conn, rsp_list) bool
  +ActiveTimeUpdate(conn)
  +NotifySendMsgFunction(conn)
  +ConnectionCleanFunction(conn)
  +CreateConnection(uint64_t conn_id) DefaultConnection
  +SetReqTimeoutHandler()
  +HandleIdleConnection()
}

class ConnPool {
  +uint16_t reactor_id_;
  +uint64_t max_conn_num_;
  +stack<uint64_t> free_;
  +vector<bool> is_in_;
  +vector<DefaultConnection*> list_;
  +map<uint64_t, uint64_t> connections_active_time_;
  +Init(max_conn_num) int
  +GenConnectionId() uint64_t
  +AddConnection(conn) bool
  +GetConnection(connection_id) DefaultConnection
  +DelConnection(connection_id)
  +RecycleConnection(connection_id)
  +RemoveIdleTimeoutConnection(idel_timeout_interval) vector
  +IsEmpty() bool
  +UpdateConnActiveState(conn_id)
  +Destory() int
  +SizeOfFree() int
}

class DefaultConnection {
  +DefaultConnectionOptions options_
  +uint64_t do_connect_timestamp_
  +uint64_t establish_timestamp_
  +struct read_buffer_
  +deque<IoMessage> io_msgs_
  +EnableReadWrite()
  +DisableReadWrite()
  +UpdateWriteEvent()
}
```

## Sequence Diagram

### Submit Send Task

应用程序发送数据时，会向 IO Task 提交一个数据发送任务，并返回一个 Future。

```mermaid
sequenceDiagram
autonumber

participant main as Main
participant fut_trans as FutureTransport
participant trans_adapter as TransportAdapter
participant io_tasks_queue as IO Tasks Queue
participant io_thread as IO Thread

main ->> main: 构造 TransInfo 配置相关回调和连接参数
main ->> fut_trans: 构造并初始化 FutureTransport
loop 为每个 IO 线程初始化一个 TransAdapter
  fut_trans ->> trans_adapter: 创建 TransAdater 实例
  trans_adapter --> fut_trans: 返回 TransAdater 实例
end
fut_trans --> main: 返回 FutureTransport 实例

main ->> main: 构造需要发送的数据 包括目标 ip 和 port
main ->> fut_trans: AsyncSendRecv(msg) 发送数据
fut_trans ->> fut_trans: 选择一个线程的 TransportAdapter 进行处理请求发送任务
fut_trans ->> fut_trans: 构造 promise future 并将 promise 记录在请求上下文中
fut_trans ->> fut_trans: 在请求上下文中记录发起请求线程的 id（xrpc 架构下的 id）
fut_trans ->> io_tasks_queue: 使用请求上下文和选择的 TransportAdapter 构造 Task 并提交
io_tasks_queue -->> fut_trans: 完成
fut_trans -->> main: 返回 future
main ->> main: 等待 future 回调处理
```

### Send Task

IO Thread 会处理数据发送任务，这包括处理连接建立、数据发送等（这里使用 ConnPoolConnector）：

```mermaid
sequenceDiagram
autonumber

participant io_tasks_queue as IO Tasks Queue
participant io_thread as IO Thread
participant trans_adapter as TransportAdapter
participant connector_manager as ConnectorManager
participant connector as ConnPoolConnector
participant conn_pool as ConnPool
participant conn as Connection

io_thread ->> io_tasks_queue: 获取 Task
io_tasks_queue -->> io_thread: 返回 Task

io_thread ->> trans_adapter: 获取一个合适的 Connector 来发送数据
trans_adapter ->> connector_manager: 获取一个 Connector
connector_manager ->> connector_manager: 获得消息目标 endpoint: {type}:{ip}:{port}
alt endpoint 存在对应的 Connector
  connector_manager -->> trans_adapter: 直接返回 connector
else endpoint 不存在对应的 Connector
  connector_manager ->> connector: 新建 ConnPoolConnector 并返回
  connector ->> connector: 启动空闲连接清理定时器
  connector ->> connector: 启动发送超时检测定时器
  connector -->> connector_manager: 返回 ConnPoolConnector 实例
  connector_manager ->> connector_manager: 保存 endpoint 对应的 connector
  connector_manager -->> trans_adapter: 直接新的 connector
end
connector_manager -->> trans_adapter: 返回 Connector
trans_adapter -->> io_thread: 返回 Connector

io_thread ->> connector: 发送数据
connector ->> conn_pool: 获得连接
alt 存在空闲连接
  conn_pool -->> connector: 返回连接
else 不存在空闲连接且没有超过限制
  connector ->> conn: 创建新的连接
  conn -->> connector: 返回连接实例
  connector ->> conn: 请求建立连接
  conn -->> connector: 返回，此时连接可能并未建立完成
  connector ->> conn_pool: 将 Connection 添加到 ConnPool 中
  conn_pool -->> connector: 返回连接
else 没有可用的连接
  conn_pool -->> connector: 返回 nullptr
end

alt 没有可用连接
  connector ->> connector: 缓存到 Pending 队列中
else 有可用连接（即便 Connection 处于连接中）
  connector ->> connector: 使用请求 id 作为 key，缓存请求上下文
  connector ->> conn: 发送消息
  conn -->> connector: 返回，此时消息可能并未发送出去
end
connector -->> io_thread: 完成
```

**注意：**

- 如果连接处于连接中，会有 Connection 对象缓存消息，并且当连接建立完成时再发送。

### Get Response

```mermaid
sequenceDiagram
autonumber

participant connector as ConnPoolConnector
participant conn_handler as ConnectionHandler
participant conn as Connection

conn ->> conn: 处理读事件，由 Reactor 感知并分发事件。
conn ->> conn: 读取数据
conn ->> conn_handler: MessageCheck()
conn_handler ->> conn_handler: 触发 【trans_info.checker_function】 回调，检查二进制数据是否为完整的包
conn_handler -->> conn: 返回

alt 响应不完整
  conn ->> conn: 放弃处理，等待下次读事件
end

conn ->> conn_handler: MessageHandle()
conn_handler ->> connector: 触发 connector.MessageHandleFunction() 回调
connector ->> connector: 触发 【trans_info.rsp_decode_function】 回调，对二进制数据反序列化
connector ->> connector: 获得请求 id，对于连接池场景，请求 id 就是连接 id
connector ->> connector: 通过请求 id 获得请求上下文
connector ->> connector: 在请求上下文中记录响应数据（反序列化后的）
connector ->> connector: 构造任务，任务就一件事，拿出 promise 并设置值，以触发 future 响应。
connector ->> connector: Dispatch() 构造任务，分发给其他线程执行任务。分发由【trans_info->rsp_dispatch_function】决定。

alt 存在 Pending 消息
  connector ->> connector: 取出消息
  connector ->> conn: 发送数据
  conn -->> connector: 返回
else 不存在 pending 消息
  connector ->> conn_pool: 将连接归还给池，以便下次使用
end
connector -->> conn_handler: 返回
conn_handler -->> conn: 返回
```

## Client Transport

`ClientTransport` 是一个抽象类，指定了开发者使用的一系列接口以便开发者可以更简单的使用 Xrpc Network。

Xrpc 的 Transport 实现均是使用的 `FutureTransport`，这里主要针对该类进行阐述。

FutureTransport 也并非直接实现 Network 相关逻辑，其主要职责是：

- 封装 TransportAdapter 的网络操作，请参考 [TransportAdapter](#transportadapter)。
- 提供同步和异步调用。
- 构造 IO 请求的 Task。
- 完善请求 STransportReqMsg 信息，例如为请求记录源线程。

### FutureTransport Initial

开发任意很少会直接使用 FutureTransport，而是在进一步封装的 `ServiceProxy` 中进行使用。ServiceProxy 是对客户端请求进行包装的，方便针对不同的应用层协议提供不同的 ServiceProxy。ServiceProxy 本身是由 ServiceProxyManager 进行初始化的：

```cpp
template <typename T>
std::shared_ptr<T> ServiceProxyManager::GetProxy(const std::string& name, const ClientConfig& conf,
                                                 const ServiceProxyOption* option_ptr) {
  // 存在 service_proxy 直接获取并返回
  auto it = service_proxys_.find(name);
  if (it != service_proxys_.end()) {
    return std::static_pointer_cast<T>(it->second);
  }

  // 构造 opitions
  std::shared_ptr<ServiceProxyOption> option = std::make_shared<ServiceProxyOption>();
  // ...

  std::shared_ptr<T> new_proxy(new T());
  new_proxy->SetServiceProxyOptionInner(option);
  // ...

  return new_proxy;
}

void ServiceProxy::SetServiceProxyOptionInner(const std::shared_ptr<ServiceProxyOption>& option) {
  // ...
  SetFutureTransportNameInner(option_->future_transport_name);
  // ...
}

void ServiceProxy::SetFutureTransportNameInner(const std::string& transport_name) {
  // init trans info
  FutureTransport::Options option;
  // 进行相关参数设置和回调处理的设置
  option.trans_info = ProxyOptionToTransInfo();

  // create and init
  ClientTransportRegistar::Create(trans_name, &future_transport_);
  future_transport_->Init(option);
}

TransInfo ServiceProxy::ProxyOptionToTransInfo() {
  TransInfo trans_info;

  // 基本参数配置 ...

  // 设置回调函数
  trans_info.conn_close_function = option_->proxy_callback.conn_close_function;
  trans_info.conn_establish_function = option_->proxy_callback.conn_establish_function;
  trans_info.msg_writedone_function = option_->proxy_callback.msg_writedone_function;
  trans_info.req_dispatch_function = option_->proxy_callback.req_dispatch_function;
  trans_info.rsp_dispatch_function = option_->proxy_callback.rsp_dispatch_function;
  trans_info.checker_function = option_->proxy_callback.checker_function;
  trans_info.rsp_decode_function = option_->proxy_callback.rsp_decode_funtion;
  trans_info.redis_conf = option_->redis_conf;
  trans_info.codec_name = codec_->Name();

  // 检查是否为完整的数据包 处理沾包拆包问题
  if (!trans_info.checker_function) {
    trans_info.checker_function = [this](const ConnectionPtr& conn, NoncontiguousBuffer& in,
                                         std::deque<std::any>& out) -> int {
      return codec_->ZeroCopyCheck(conn, in, out);
    };
  }

  // 响应结构化函数
  if (!trans_info.rsp_decode_function) {
    trans_info.rsp_decode_function = [this](std::any&& in, ProtocolPtr& out) -> bool {
      out = std::move(codec_->CreateResponsePtr());
      return codec_->ZeroCopyDecode(nullptr, std::move(in), out);
    };
  }

  // 默认的派发函数使用配置中指定的 threadmodel，如希望采用其他派发策略可重写派发函数
  if (!trans_info.rsp_dispatch_function) {
    trans_info.rsp_dispatch_function = [this, thread_model](Task* task) {
      // ...
    };
  }

  return trans_info;
}
```

### Async Send Impl

发送异步请求使用的是 AsyncSendRecv 接口，参数要求为 [STransportReqMsg](#stransportreqmsg)。

```cpp
Future<STransportRspMsg> FutureTransport::AsyncSendRecv(STransportReqMsg* msg) {
  assert(msg->extend_info);
  
  // ... backup request 逻辑 省略

  // 选择执行网络操作的 IO 线程
  uint16_t id = SelectTransportAdapter(msg);
  return AsyncSendRecvImp(msg, id);
}
```

发起 AsyncSendRecv 请求的线程构建 Request Task ，并提交给 IO Thread 执行 Request Task，那么 FutureTransport 是如何选择运行 Request Task 的 IO Thread 呢？这就是根据 `SelectTransportAdapter` 进行选择的：

```cpp
uint16_t FutureTransport::SelectTransportAdapter(STransportReqMsg* msg) {
  auto* current_thread = WorkerThread::GetCurrentWorkerThread();

  // 非 Xrpc Thread 线程发起请求，轮询其中一个 IO 线程进行处理
  if (!current_thread) {
    msg->extend_info->client_extend_info.dispatch_info->src_thread_id = -1;
    return SelectIOThread(trans_adapters_.size()); 
  }

  msg->extend_info->client_extend_info.dispatch_info->src_thread_model_id = current_thread->GroupId();
  msg->extend_info->client_extend_info.dispatch_info->src_thread_id = GetLogicId(current_thread);

  // 请求由 Xrpc IO Thread 发起，则直接选择线程自己的 ID 返回，即自己处理这个 Request Task
  if (current_thread->GetRole() != WorkerThread::Role::HANDLE) {
    return GetLogicId(current_thread);
  }

  // 请求由 Xrpc Handle Thread 发起，则轮询其中一个 IO 线程进行处理
  return SelectIOThread(trans_adapters_.size());
}

uint16_t FutureTransport::SelectIOThread(const uint16_t io_thread_num) {
  // 自定义了 Request Task 的分发方式，则交给自定义方法处理
  if (options_.trans_info.req_dispatch_function) {
    return options_.trans_info.req_dispatch_function(io_thread_num);
  }

  // 默认进行轮询
  return Roll(io_thread_num);
}

uint16_t FutureTransport::Roll(const uint16_t io_thread_num) {
  uint16_t index = io_index_++ % io_thread_num;
  return index;
}
```

这里通过 `msg->extend_info->client_extend_info.dispatch_info->src_thread_id` 记录了发起线程的 ID，这是为了方便后面处理响应时，将其交给发起线程进行处理（虽然这种处理方式并不一定合理）。

应用层感知 Request Task 是否收到回包处理依赖于 Promise Future 模式，在 `AsyncSendRecvImp` 实现中将会生成 Promise，并返回 Future：

```cpp
Future<STransportRspMsg> FutureTransport::AsyncSendRecvImp(STransportReqMsg* msg,
                                                           const uint16_t id) {

  // 构造 Promise 和 Future
  auto promise_ptr = new Promise<STransportRspMsg>();
  auto fut = promise_ptr->get_future();

  // 记录 Promise 在 Message 中，处理响应时会使用 Promise
  msg->extend_info->client_extend_info.promise = promise_ptr;

  auto ret = SendRequest(msg, id, XrpcCallType::XRPC_UNARY_CALL);

  // 队列满时直接返回异常
  if (ret == TaskRetCode::QUEUE_FULL) {
    return MakeExceptionFuture<STransportRspMsg>(
        CommonException("io task queue is full, maybe overload", TaskRetCode::QUEUE_FULL));
  }

  return fut;
}
```

在 `SendRequest` 中会进行 Task 的构造以及 Task 的提交，Task 具体会依赖于 TransportAdapter 进行网络请求的发送。这里构造 Task 时会使用先前通过 `SelectTransportAdapter` 得到的线程 ID，设置 `task->dst_thread_key`，以分发 Task 到对应的 IO 线程：

```cpp
int FutureTransport::SendRequest(STransportReqMsg* msg, uint16_t id, XrpcCallType call_type) {
  Task* task = CreateTransportRequestTask(msg, id, call_type);
  TaskResult result = options_.thread_model->SubmitIoTask(task);
  return result.ret;
}

Task* FutureTransport::CreateTransportRequestTask(STransportReqMsg* msg, const uint16_t id,
                                                  XrpcCallType call_type) {
  Task* task = new Task();
  task->task_type = TaskType::TRANSPORT_REQUEST;
  task->task = msg;
  task->dst_thread_key = id;
  task->group_id = options_.thread_model->GetThreadModelId();

  // 设置对应的handler
  auto trans_adapter = trans_adapters_[id];

  task->handler = [trans_adapter, msg, call_type = std::move(call_type)](Task* task) mutable {
    switch (call_type) {
      case XrpcCallType::XRPC_UNARY_CALL:
        trans_adapter->GetConnector(msg)->SendReqMsg(msg);
        break;
      case XrpcCallType::XRPC_ONEWAY_CALL:
        trans_adapter->GetConnector(msg)->SendOnly(msg);
        delete msg;
        break;
      default:
        assert(0 && "No support yet");
        break;
    }
  };

  return task;
}
```

### Sync Send Impl

Transport 的同步调用是基于其异步接口实现的，主要依赖于 `future.Wait()` 机制：

```cpp
int FutureTransport::SendRecv(STransportReqMsg* req_msg, STransportRspMsg* rsp_msg) {
  auto fut = AsyncSendRecv(req_msg);

  // 等待处理超时
  if (!fut.Wait(req_msg->basic_info->timeout)) {
    return -1;
  }

  // 处理失败 直接返回 -1
  if (!fut.is_ready()) {
    return -1;
  }

  // 处理成功
  rsp_msg->msg = std::move(std::get<0>(fut.GetValue()).msg);
  return 0;
}
```

### SendOnly

FutureTransport 支持只发送数据而忽略对响应的等待，这可能在某些 UDP 的场景中较为常见。本质上是忽略对 promise 来实现：

```cpp
int FutureTransport::SendOnly(STransportReqMsg* msg) {
  uint16_t id = SelectIOThread(trans_adapters_.size());
  return SendRequest(msg, id, XrpcCallType::XRPC_ONEWAY_CALL);
}
```

### Backup Request

有时为了保证可用性和低时延，需要同时访问两路服务，哪个先返回就取哪个，Xrpc 的实现策略是：

> 设置一个合理的resend time，当一个请求在resend time内超时或失败了，再发送第二个请求，然后取先返回的结果。这也是bRPC backup request的实现方式。

在 FutureTransport 若信息配置了 Backup Request 则会使用该逻辑：

```cpp
Future<STransportRspMsg> FutureTransport::AsyncSendRecv(STransportReqMsg* msg) {
  assert(msg->extend_info);
  auto retry_info = msg->extend_info->client_extend_info.retry_info;
  if (retry_info && retry_info->retry_policy == RetryInfo::RetryPolicy::BACKUP_REQUEST) {
    return AsyncSendRecvForBackupRequest(msg);
  }

  // ...
}

// 下面的代码忽略了非常多的细节
Future<STransportRspMsg> FutureTransport::AsyncSendRecvForBackupRequest(STransportReqMsg* msg) {
  auto& client_extend_info = msg->extend_info->client_extend_info;

  // 创建用于通知应用层的 promise/future
  auto promise_ptr = new Promise<STransportRspMsg>();
  auto fut = promise_ptr->get_future();

  // 设置第一个请求的 promise 和回调
  client_extend_info.promise = new Promise<STransportRspMsg>();
  auto fut_first = client_extend_info.promise->get_future();

  // 设置 backup promise 根据 First Promise 的情况判断 backup resend 是否发送
  client_extend_info.backup_promise = new Promise<bool>();
  auto backup_fut = client_extend_info.backup_promise->get_future();
  backup_fut.Then([=](Future<bool>&& fut) mutable {

    // 正常请求成功，直接返回
    if (fut.is_ready()) {
      // 触发应用层 future 回调
      promise_ptr->SetValue(fut_first.GetValue());
      return MakeReadyFuture<>();
    }

    // 失败，执行 resend 逻辑
    std::vector<Future<STransportRspMsg>> vecs;
    vecs.emplace_back(std::move(fut_first));  // fut_first直接放入

    // 必须在同一个 io 线程中发送数据
    uint16_t new_id = SelectTransportAdapter(msg, id);

    // 从第一个 backup 地址开始，故 i = 1
    auto& retry_info = msg->extend_info->client_extend_info.retry_info;
    for (int i = 1; i < retry_info->back_addr.size(); i++) {
      auto new_fut = AsyncSendRecvImp(msg, new_id)
                         .Then([new_msg, retry_info](Future<STransportRspMsg>&& fut) {
                           return std::move(fut);
                         });

      vecs.emplace_back(std::move(new_fut));
    }

    return WhenAnyWithoutException(vecs.begin(), vecs.end())
        .Then([=](Future<size_t, std::tuple<STransportRspMsg>>&& fut) {
          // 通知应用层 future 回调
          if (fut.is_ready()) {
            promise_ptr->SetValue(std::move(std::get<1>(result)));
          } else {
            promise_ptr->SetException(fut.GetException());
          }
          return MakeReadyFuture<>();
        });
  });

  // 发起请求
  uint16_t id = SelectTransportAdapter(msg);
  int ret = SendRequest(msg, id, XrpcCallType::XRPC_UNARY_CALL);
  return fut;
}
```

在 Connector 中会负责通过设置 backup_promise 以发起重试，细节请参考 [Connector](#connector)。

## TransportAdapter

TransportAdapter 封装了 ConnectorManager 的相关操作，每个 IO 线程都有独立的 TransportAdapter。

有多少 IO 线程就有多少 TransportAdapter，该对象在 FutureTransport 中进行初始化，并且数组维护在 FutureTransport 中。数组下标和 IO 线程的线程 ID 是一一对应的（此线程 ID 并非 Linux 线程 ID，而是 Xrpc 为线程赋予的）：

```cpp
int FutureTransport::Init(const std::any& params) {
  Options options = std::any_cast<const FutureTransport::Options&>(params);
  options_ = options;

  // 根据 IO 线程数初始化 trans_adapters_
  for (auto& io_thread : options_.thread_model->GetWorkerThreads(WorkerThread::Role::IO)) {
    TransportAdapter::Options transport_adapter_option;
    transport_adapter_option.io_model = io_thread->GetIoModel();
    transport_adapter_option.trans_info = &(options_.trans_info);

    trans_adapters_.emplace_back(new TransportAdapter(std::move(transport_adapter_option)));
  }

  return 0;
}
```

显而易见，`trans_adapters[i]` 是第 i 个 IO 线程的 trans_adatpter。

TransportAdapter 很简单，就是代理了 ConnectorManager 的相关动作，最核心的动作就是获得 Connector。

```cpp
Connector* TransportAdapter::GetConnector(STransportReqMsg* req_msg) {
  return connector_mgr_->GetConnector(req_msg);
}
```

TransportAdapterOptions 没啥用，Connector 都记录了这些信息的。

## ConnectorManager

ConnectorManager 用于管理 Connector，而 Connector 是真正负责封装网络操作的对象。

ConnectorManager 会根据配置初始化连接复用类型的 Connector 或连接池类型的 Connector。

ConnectorManager 建立的 Connector 池和远程端点关联在一起：

```text
endpointId_to_connector_[{conn_type}:{ip}:{port}] = Connector
```

ConnectorManager 中的 Connector 属于懒加载，在用到时才会去进行初始化：

```cpp
Connector* ConnectorManager::GetConnector(STransportReqMsg* req_msg) {
  size_t len = 64;
  std::string endpointId = Foramt("{type}:{ip}:{port}",
                                  options_.trans_info->conn_type,
                                  req_msg->basic_info->addr.ip,
                                  req_msg->basic_info->addr.port);

  // Connector 已经存在，直接返回并使用
  auto it = endpointId_to_connector_.find(endpointId);
  if (it != endpointId_to_connector_.end()) {
    return it->second;
  }

  // 指定是连接复用还是连接池模式,创建对应连接模式的Connector
  Connector::Options connector_options;
  connector_options.io_model = options_.io_model;
  connector_options.trans_info = options_.trans_info;
  connector_options.peer_addr = NetworkAddress(std::string_view(req_msg->basic_info->addr.ip),
                                               req_msg->basic_info->addr.port,
                                               NetworkAddress::IpType::ipv4);

  Connector* newConnector = nullptr;
  if (connector_options.trans_info->conn_type == ConnectionType::UDP) {
    // UDP
    newConnector = new UdpConnector(connector_options);
  } else if (options_.trans_info->is_complex_conn) {
    // TCP 连接复用模式
    newConnector = new ConnComplexConnector(connector_options);
  } else {
    // TCP 连接池模式
    newConnector = new ConnPoolConnector(connector_options);
  }

  endpointId_to_connector_[endpointId] = newConnector;
  return newConnector;
}
```

## Connector

Connector 作为抽象类实现了核心网络逻辑，包括：

- 创建 TCP/UDP 连接的逻辑
- 将请求的上下文进行保存
- 网络请求逻辑
- 分发网络响应的处理 Task

Connector 的子类 ConnComplexConnector 和 ConnPoolConnector 主要是实现：

- 如何选择发起请求的连接
- 如何构造连接的 conn_id
- 如何处理请求的响应

对于 Connector 创建 TCP 连接的逻辑，会由子类根据自己的策略调用构建 Connector。

创建连接的核心是构造 Connection Options，设置连接的处理回调，并建立连接：

```cpp
DefaultConnection* Connector::CreateTcpConnection(uint64_t conn_id) {
  // 设置连接参数以及连接相关事件的回调
  DefaultConnection::Options options = MakeConnectionOption(conn_id);

  // 设置连接的 Socket
  options.options.socket = Socket::CreateTcpSocket(options_.peer_addr.IsIpv6());

  // 设置连接的 IO Handler，IO Handler 是如何使用 fd 进行相关 io 操作的封装
  options.options.io_handler = IoHandlerFactory::GetInstance()->Create(options.options.socket.GetFd(),
                                                                       *(options_.trans_info));

  DefaultConnection* conn = new TcpConnection(options);
  conn->DoConnect();

  return conn;
}

DefaultConnection::Options Connector::MakeConnectionOption(uint64_t conn_id) {
  // 构造连接参数
  DefaultConnection::Options options;
  // Connection::Options options;
  options.recv_buffer_size = options_.trans_info->recv_buffer_size;
  options.options.max_packet_size = options_.trans_info->max_packet_size;
  options.merge_send_data_size = options_.trans_info->merge_send_data_size;
  options.options.event_handler_id = options_.io_model->GetReactor()->GenEventHandlerId();
  options.options.reactor = options_.io_model->GetReactor();
  options.options.type = options_.trans_info->conn_type;
  options.options.conn_id = conn_id;
  options.options.client = true;

  // 客户端ConnectionInfo只需要对端的IP/Port这些信息
  ConnectionInfo connection_info;
  connection_info.remote_addr = options_.peer_addr;
  options.options.conn_info = std::move(connection_info);

  // 设置 function
  // trans_info 里本身就包含了很多回调处理，例如检查响应是否为完整的 Packet 等
  auto* conn_handler = new FutureConnectionHandler(options_.trans_info);

  conn_handler->SetNotifyMsgSendFunc([this](const ConnectionPtr& conn) { return this->NotifySendMsgFunction(conn); });
  conn_handler->SetCleanFunc([this](const ConnectionPtr& conn) { this->ConnectionCleanFunction(conn); });
  conn_handler->SetTimeUpdateFunc([this](const ConnectionPtr& conn) { this->ActiveTimeUpdate(conn); });
  conn_handler->SetPipelineCountGetFunc([this](const ConnectionPtr conn) { return this->GetPipelineCount(conn); });

  conn_handler->SetMsgHandleFunc([this](const ConnectionPtr& conn, std::deque<std::any>& data) {
    // MessageHandleFunction 由 Connector 的子类实现
    return this->MessageHandleFunction(conn, data);
  });

  options.options.conn_handler = conn_handler;

  return options;
}
```

对于 FutureConnectionHandler 请参考 [FutureConnectionHandler](#futureconnectionhandler)。

对于请求上下文的保存，这也是由子类进行调用，上下文保存所需要的 request_id 也由子类根据自的策略生成。需要注意的是，上下文有两种：

- 正常发起请求，请求的上下文会进行保存，并且具备超时时间：

  ```cpp
  void Connector::PushToSendReqTimeoutQueue(STransportReqMsg* req_msg) {
    // req_msg 就是请求上下文，需要保存
  
    // 上下文空间满了，分发异常作为请求的响应
    if (send_req_timeout_queue_->Size() > send_queue_size_limit_) {
      DispatchException(req_msg, XrpcRetCode::XRPC_CLIENT_INVOKE_TIMEOUT_ERR, "Client Overload in Send Queue");
      return;
    }
  
    // 超时时间计算，如果为backup request请求的话，取 resend timeout
    auto& client_extend_info = req_msg->extend_info->client_extend_info;
    int64_t timeout = client_extend_info.retry_info && client_extend_info.backup_promise
                          ? client_extend_info.retry_info->delay
                          : req_msg->basic_info->timeout;
    // 加上起始时刻
    timeout += req_msg->basic_info->begin_timestamp;
  
    // 添加上下文到内存 request_id 就是 req_msg->basic_info->seq_id
    send_req_timeout_queue_->Push(req_msg, req_msg->basic_info->seq_id, timeout, false);
  }
  
  STransportReqMsg* Connector::PopSendTimeoutQueue(uint32_t request_id) {
    // 根据 request_id 获得请求上下文
    STransportReqMsg* msg = nullptr;
    send_req_timeout_queue_->Erase(request_id, msg);
    return msg;
  }
  ```

- 由于连接正在建立，上下文会存放到 Pending 队列中，并且具备超时时间：

  ```cpp
  void Connector::PushToPendingTimeoutQueue(STransportReqMsg* req_msg) {
    if (pending_req_timeout_queue_->Size() > pending_queue_size_limit_) {
      DispatchException(req_msg, XrpcRetCode::XRPC_CLIENT_INVOKE_TIMEOUT_ERR, "Client Overload in Pending Queue");
      return;
    }
  
    // 超时时间计算，如果为backup request请求的话，取resend timeout
    assert(req_msg->extend_info);
    auto& client_extend_info = req_msg->extend_info->client_extend_info;
    int64_t timeout = client_extend_info.retry_info && client_extend_info.backup_promise
                          ? client_extend_info.retry_info->delay
                          : req_msg->basic_info->timeout;
    // 加上起始时刻
    timeout += req_msg->basic_info->begin_timestamp;
  
    pending_req_timeout_queue_->Push(req_msg, req_msg->basic_info->seq_id, timeout, false);
  }
  
  bool Connector::PopPendingSendTask(STransportReqMsg** req_msg) {
    if (pending_req_timeout_queue_->GetSend(*req_msg)) {
      pending_req_timeout_queue_->PopSend(true);
      return true;
    }
    return false;
  }
  ```

发送请求，核心就是用 conn->Send 的方法进行发送：

```cpp
int Connector::DoSend(STransportReqMsg* req_msg, Connection* conn) {
  IoMessage message;
  message.buffer = std::move(req_msg->send_data);
  message.seq_id = req_msg->basic_info->seq_id;
  int ret = conn->Send(std::move(message));
  if (ret != 0) {
    std::string error = "network send error, peer addr:";
    error += options_.peer_addr.ToString();
    PopSendTimeoutQueue(req_msg->basic_info->seq_id);
    DispatchException(req_msg, XrpcRetCode::XRPC_CLIENT_NETWORK_ERR, std::move(error));
  }
  return ret;
}

int Connector::SendOnly(STransportReqMsg* req_msg) {
  auto* conn = GetConnection(req_msg);
  if (conn) {
    IoMessage message;
    // default tcp connection 下只需要设置 data 字段
    assert(req_msg);
    message.buffer = std::move(req_msg->send_data);
    message.seq_id = req_msg->basic_info->seq_id;
    return conn->Send(std::move(message));
  }
  return -1;
}
```

当请求存在响应时，会将响应处理打包为一个 Task，并分发给相应线程进行处理，核心逻辑是：

- 使用 trans_info 中设置的 task 分发函数，将 task 分发给线程
- task 通过设置 promise 来通知 future 回调

```cpp
void Connector::DispatchResponse(STransportReqMsg* req_msg, STransportRspMsg&& rsp_msg) {
  // 这里的响应处理是设置构造一个task，其中 handler 为 promise 设置 value，然后提交到业务 HandleModel 的 task 队列中
  Task* task = new Task();
  task->task_type = TaskType::TRANSPORT_RESPONSE;
  task->task = req_msg;
  // 设置对应的handler
  task->handler = [req_msg, rsp_msg = std::move(rsp_msg)](Task* task) mutable {
    auto promise = req_msg->extend_info->client_extend_info.promise;

    // 设置 promise 触发 future 的回调
    promise->SetValue(std::move(rsp_msg));

    // 首个请求成功，直接取消resend回调，结束调用
    auto backup_promise = req_msg->extend_info->client_extend_info.backup_promise;
    if (backup_promise) {
      NotifyBackupRequestOver(backup_promise);
    }
  };

  // 执行上层设置的 rsp_dispatch_function，实现 Task 的分发
  options_.trans_info->rsp_dispatch_function(task);
}
```

响应如果失败，也会进行分发，触发 future 回调：

```cpp
void Connector::DispatchException(STransportReqMsg* req_msg, int ret, std::string&& err_msg) {
  // 这里的响应处理是设置构造一个task，其中handler为promise设置value，然后提交到业务HandleModel的task队列中
  Task* task = new Task();
  task->task_type = TaskType::TRANSPORT_RESPONSE;
  task->task = req_msg;
  // 设置对应的handler
  task->handler = [req_msg, ret, msg = std::move(err_msg)](Task* task) mutable {
    // 如果存在 backup 则触发 backup 的请求
    auto backup_promise = req_msg->extend_info->client_extend_info.backup_promise;
    if (backup_promise) {
      Exception ex(CommonException("Invoke failed", XRPC_INVOKE_UNKNOWN_ERR));
      NotifyBackupRequestResend(ex, req_msg->extend_info->client_extend_info.backup_promise);
    }

    // promise 失败
    auto promise = req_msg->extend_info->client_extend_info.promise;
    promise->SetException(ex);
  };

  // 执行上层设置的rsp_dispatch_function，实现Task的分发
  options_.trans_info->rsp_dispatch_function(task);
}
```

### ConnPoolConnector

ConnPoolConnector 是连接池 Connector，其包含了一组连接，并通过连接池进行并发网络请求。ConnPoolConnector 建立时会注册两个定时器：

1. 用于清理空闲连接的定时器。即连接长时间没有网络事件会自动关闭连接。
1. 用于检查

```cpp
ConnPoolConnector::ConnPoolConnector(const Options& options)
    : Connector(options), conn_pool_(options.io_model->GetReactor()->Id()) {
  conn_pool_.Init(options_.trans_info->max_conn_num);

  // 注册空闲连接清理定时任务，每秒执行 1 词
  uint32_t timer_index = options_.io_model->GetReactor()->AddTimerAfter(0, 10000, [this]() { this->RemoveIdleConnection(); });
  timer_index_vec_.push_back(timer_index);

  // 注册请求队列超时检测定时任务(包括已发送和 pending 中的请求)
  // 每十秒执行一次
  timer_index = options_.io_model->GetReactor()->AddTimerAfter(0, 10, [this]() { this->SetReqTimeoutHandler(); });
  timer_index_vec_.push_back(timer_index);
}

void ConnPoolConnector::RemoveIdleConnection() {
  // 从连接池中获得满足空闲时间条件的连接
  auto conn_vec = conn_pool_.RemoveIdleTimeoutConnection(options_.trans_info->connection_idle_timeout);
  for (auto conn : conn_vec) {
    // 判断连接是否还有请求在等待应答，避免因 timeout 长于空闲连接超时时间而误删连接
    if (!send_req_timeout_queue_->IsInQueue(conn->GetConnId() & kConnIdMask)) {
      conn->DoClose();
    }
  }
}

void ConnPoolConnector::SetReqTimeoutHandler() {
  STransportReqMsg* msg = nullptr;

  // send_req_timeout_queue_ 是发送中但未收到响应的队列，这也是存放的请求上下文
  // 每次迭代出一个超时的请求超时下文
  while (send_req_timeout_queue_->Timeout(msg)) {

    // 如果存在 backup promise 则触发 backup 请求的发送
    if (msg->extend_info->client_extend_info.backup_promise) {
      Exception ex(CommonException("Resend timeout", XRPC_CLIENT_INVOKE_TIMEOUT_ERR));
      Connector::NotifyBackupRequestResend(ex, msg->extend_info->client_extend_info.backup_promise);

      // 把请求包重新放回队列:需要重新设置超时时间
      msg->basic_info->timeout -= msg->extend_info->client_extend_info.retry_info->delay;
      PushToSendReqTimeoutQueue(msg);
      continue;
    }

    // 派发超时响应
    std::string error = "Future invoke timeout peeraddr= " + options_.peer_addr.ToString();
    DispatchException(msg, XrpcRetCode::XRPC_CLIENT_INVOKE_TIMEOUT_ERR, std::move(error));

    // 连接池模式下，请求超时，需要关闭连接(避免响应串包)
    // 如果继续用这个连接发数据，收到的响应可能是之前请求的，但是之前请求的上下文已经因为超时而删除
    conn_pool_.GetConnection(msg->basic_info->connection_id)->DoClose();
  }

  // pending_req_timeout_queue_ 是由于连接未建立完成导致无法发送数据而将数据缓存的队列
  // 每次迭代出一个超时的请求超时下文
  while (pending_req_timeout_queue_->Timeout(msg)) {
    // 如果存在 backup promise 则触发 backup 请求的发送
    if (msg->extend_info->client_extend_info.backup_promise) {
      Exception ex(CommonException("Resend pending timeout", XRPC_CLIENT_INVOKE_TIMEOUT_ERR));
      Connector::NotifyBackupRequestResend(ex, msg->extend_info->client_extend_info.backup_promise);

      // 把请求包重新放回队列:需要重新设置超时时间
      msg->basic_info->timeout -= msg->extend_info->client_extend_info.retry_info->delay;
      PushToPendingTimeoutQueue(msg);
      continue;
    }

    // 派发超时响应
    DispatchException(msg, XrpcRetCode::XRPC_CLIENT_INVOKE_TIMEOUT_ERR, "Future invoke timeout before send");
    // 连接池模式下，请求超时，因为 pending 队列中的请求并没有发送出去，所以不需要将 pending 队列中的连接关闭
  }
}
```

ConnPoolConnector 最核心的逻辑之一是数据发送，其关键点是：

- 请求上下文的 id 是连接 ID，这是自然的，因为一个连接同一时间只会发送一个请求。
- 发送数据时，若连接池中没有可用的连接会创建一个新的连接。
- 如果连接池已经耗尽，无法创建新的连接，请求会缓存在 pending_req_timeout_queue_ 队列中，等待存在可用连接时发送。

```cpp
int ConnPoolConnector::SendReqMsg(STransportReqMsg* req_msg) {
  // 连接达到上限且全部分配,放到 pending 队列
  DefaultConnection* conn = GetConnection(req_msg);
  if (!conn) {
    PushToPendingTimeoutQueue(req_msg);
    return 0;
  }

  // 连接始终无法建立成功，将连接关掉
  if (conn->GetConnectionState() == DefaultConnection::ConnectionState::kConnecting &&
        kConnectInterval + conn->GetDoConnectTimestamp() < TimeProvider::GetNowMs()) {
      ushToPendingTimeoutQueue(req_msg);
      conn->DoClose();  // 触发清理操作
      return 0;
  }


  // 使用连接 ID 作为请求上下文的 ID
  req_msg->basic_info->connection_id = conn->GetConnId();
  req_msg->basic_info->seq_id = (conn->GetConnId() & kConnIdMask);

  // 连接可用，直接发到请求超时队列中
  PushToSendReqTimeoutQueue(req_msg);
  return DoSend(req_msg, conn);
}

DefaultConnection* ConnPoolConnector::GetConnection(STransportReqMsg* req_msg) {
  // 连接 ID 用尽，直接返回 nullptr
  uint64_t conn_id = conn_pool_.GenConnectionId();
  if (conn_id == 0) {
    return nullptr;
  }

  // 根据连接 ID 获得连接
  DefaultConnection* conn = conn_pool_.GetConnection(conn_id);
  if (conn != nullptr) {
    return conn;
  }

  // 连接 ID 对应的连接为空 则创建连接
  conn = CreateConnection(conn_id);
  if (conn->GetConnectionState() == TcpConnection::ConnectionState::kUnconnected) {
    // 连接创建失败
    conn_pool_.DelConnection(conn_id);
    return nullptr;
  }

  conn_pool_.AddConnection(conn);
  return conn;
}
```

ConnPoolConnector 的另一个核心逻辑是处理请求的响应，其关键点是：

- 解析响应。
- 获取请求上下文进行处理。
- 分发响应 Task 处理。
- 处理完响应 Task 分发后会直接取 pending_req_timeout_queue_ 中的消息进行发送。
- 若连接没有其他事物需要处理，则将其回收至连接池中。

```cpp
bool ConnPoolConnector::MessageHandleFunction(const ConnectionPtr& conn,
                                              std::deque<std::any>& rsp_list) {
  // 迭代所有响应消息
  for (auto&& rsp_buf : rsp_list) {
    // 解析响应到 rsp_protocol
    ProtocolPtr rsp_protocol;
    bool ret = options_.trans_info->rsp_decode_function(std::move(rsp_buf), rsp_protocol);

    // 通过 connection id 获得请求上下文
    uint32_t request_id = (conn->GetConnId() & kConnIdMask);
    STransportReqMsg* msg = PopSendTimeoutQueue(request_id);

    // 由于某些原因导致请求上下文不存在，直接调过对响应的处理
    if (!msg) {
      continue;
    }

    // 解析响应失败
    if (!ret) {
      std::string error = "Decode Failed peeraddr= " + options_.peer_addr.ToString();
      DispatchException(msg, XrpcRetCode::XRPC_CLIENT_DECODE_ERR, std::move(error));
      conn->DoClose();
      continue;
    }

    // 分发响应
    STransportRspMsg rsp_msg;
    rsp_msg.msg = std::move(rsp_protocol);
    DispatchResponse(msg, std::move(rsp_msg));
  }

  // 发送 Pending 队列中的连接
  // 如果 Pending 为空，将连接归还到连接池
  if (!SendPendingMsg(conn)) conn_pool_.RecycleConnection(conn->GetConnId());
  return true;
}

bool ConnPoolConnector::SendPendingMsg(ConnectionPtr conn) {

  // 如果不存在 pending 的请求 直接返回
  STransportReqMsg* req_msg = nullptr;
  if (!PopPendingSendTask(&req_msg)) {
    return false;
  }

  // 连接复用模式下，发送之前需要将请求的 request_id 设置为连接 id
  req_msg->basic_info->connection_id = conn->GetConnId();
  req_msg->basic_info->seq_id = (conn->GetConnId() & kConnIdMask);
  // 连接可用之后，把pending超时队列中的请求，移到请求超时队列中,并发送
  PushToSendReqTimeoutQueue(req_msg);

  // 使用Connection发送请求
  DoSend(req_msg, conn);

  return true;
}
```

连接保活事件会更新相关连接的活跃状态：

```cpp
void ActiveTimeUpdate(Connection* conn) override {
  conn_pool_.UpdateConnActiveState(conn->GetConnId());
}
```

#### ConnPool

ConnPool 对于 ConnPoolConnector 是一个很重要的类，连接 ID 的构建、连接保活、连接池维护都是依赖于该类。

ConnPool 初始化时会先明确连接池大小，并初始化连接序号，魔数 Magic：

```cpp
// 默认连接池大小时 10w 连接
ConnPool::ConnPool(uint16_t reactor_id) : reactor_id_(reactor_id), max_conn_num_(100000), magic_(GenMagic(reactor_id)) {
  Init(max_conn_num_);
}

// 连接池通常会由外层主动调用 Init 重新进行一次构造
void ConnPool::Init(uint32_t max_conn_num) {
  if (!free_.empty()) {
    std::stack<uint64_t> empty;
    std::swap(free_, empty);
  }

  // list 建立了连接序号和连接的映射
  list_.clear();
  list_.resize(max_conn_num + 1);

  // is_in_ 标识连接序号是否在连接池中
  // is_in_[i] == true 标识序号 i 的连接在连接池中，未使用
  is_in_.clear();
  is_in_.resize(max_conn_num + 1);

  for (uint64_t i = 1; i <= max_conn_num; ++i) {
    list_[i] = nullptr;
    free_.push(i);
    is_in_[i] = true;
  }

  max_conn_num_ = max_conn_num;
}
```

需要注意的时，连接 ID 并非连接序号，而是关联了一个魔数，这是用于将不同 Reactor 的连接 ID 进行隔离，连接 ID 是一个 48 Bit 的结构：

```text
+---------------------------------------+
|                48 Bit                 |
+-------------------+-------------------+
|    High 16 Bit    |    Low 32 Bit     |
+-------------------+-------------------+
| Magic(reactor_id) | Magic(reactor_id) |
+-------------------+-------------------+
```

生成连接 ID，向连接池中添加一个连接：

```cpp
uint64_t ConnPool::GenConnectionId() {
  // 连接池中的连接序号耗尽
  if (free_.empty()) {
    return 0;
  }

  uint64_t uid = free_.top();
  free_.pop();

  // 连接处于使用中
  is_in_[uid] = false;

  // 构造连接 ID
  return magic_ | uid;
}

bool ConnPool::AddConnection(DefaultConnection* conn) {
  auto connection_id = conn->GetConnId();
  auto magic = 0x0000FFFF00000000 & connection_id;
  auto uid = 0x00000000FFFFFFFF & connection_id;

  assert(magic == magic_ && uid > 0 && uid <= max_conn_num_);

  // 序号对应的连接已经存在，不能添加，失败
  if (list_[uid] != nullptr) {
    return false;
  }

  // 序号对应的连接保存，记录连接活跃时间
  list_[uid] = conn;
  connections_active_time_[uid] = TimeProvider::GetNowMs();
  return true;
}

DefaultConnection* ConnPool::GetConnection(uint64_t connection_id) {
  auto magic = 0x0000FFFF00000000 & connection_id;
  auto uid = 0x00000000FFFFFFFF & connection_id;

  assert(magic == magic_ && uid > 0 && uid <= max_conn_num_);
  return list_[uid];
}

// 连接清理或者连接创建失败都会把连接从池中删除，连接 ID 归还连接池
void ConnPool::DelConnection(uint64_t connection_id) {
  auto magic = 0x0000FFFF00000000 & connection_id;
  auto uid = 0x00000000FFFFFFFF & connection_id;

  assert(magic == magic_ && uid > 0 && uid <= max_conn_num_);

  list_[uid] = nullptr;

  // 连接序号不在池中，归还序号
  if (!is_in_[uid]) {
    free_.push(uid);
    is_in_[uid] = true;
  }

  // 连接活跃时间记录中剔除
  auto it = connections_active_time_.find(uid);
  if (it != connections_active_time_.end()) {
    connections_active_time_.erase(it);
  }
}
```

当连接使用完需要归还连接序号给连接池，方便下次再使用该连接：

```cpp
void ConnPool::RecycleConnection(uint64_t connection_id) {
  auto magic = 0x0000FFFF00000000 & connection_id;
  auto uid = 0x00000000FFFFFFFF & connection_id;

  assert(magic == magic_ && uid > 0 && uid <= max_conn_num_);

  if (!is_in_[uid]) {
    is_in_[uid] = true;
    free_.push(uid);
  }
}
```

当发生了网络事件，会触发保活事件，让 ConnPool 刷新时间：

```cpp
void ConnPool::UpdateConnActiveState(uint64_t conn_id) {
  auto magic = 0x0000FFFF00000000 & conn_id;
  auto uid = 0x00000000FFFFFFFF & conn_id;

  assert(magic == magic_ && uid > 0 && uid <= max_conn_num_);

  auto it = connections_active_time_.find(uid);
  if (it != connections_active_time_.end()) it->second = TimeProvider::GetNowMs();
}
```

每秒会遍历 connections_active_time_，找出空闲超时的连接：

```cpp
std::vector<DefaultConnection*> ConnPool::RemoveIdleTimeoutConnection(uint64_t idel_timeout_interval) {
  uint64_t now = TimeProvider::GetNowMs();

  std::vector<DefaultConnection*> conn_to_del;
  auto it = connections_active_time_.begin();
  while (it != connections_active_time_.end()) {
    if (now > it->second && now - it->second >= idel_timeout_interval) {
      conn_to_del.push_back(list_[it->first]);
    }
    it++;
  }
  return conn_to_del;
}
```

### ConnComplexConnector

ConnComplexConnector 会建立一个连接，该连接支持同时发送多个请求，也因此 ConnComplexConnector 每次会生成一个请求 ID，用于保存使用的请求上下文，响应也要求足以解析出该上下文 ID，以取出对应的请求上下文进行处理。

对于 ConnComplexConnector 因为它只会使用一个连接，所以 Xrpc 固定给连接 ID 设置为 0.

ConnComplexConnector 初始化和 ConnPoolConnector 类似，主要是用于注册空闲检查和超时检查的定时器，不同的是，ConnComplexConnector 在建立时就会创建连接：

```cpp
ConnComplexConnector::ConnComplexConnector(const Options& options) : Connector(options){

  // 创建连接，连接 ID 为 0
  connection_ = CreateConnection(0);

  // 注册空闲连接清理定时任务
  uint32_t timer_index = options_.io_model->GetReactor()->AddTimerAfter(0, 10000, [this]() { this->HandleIdleConnection(); });
  timer_index_vec_.push_back(timer_index);

  // 注册请求队列超时检测定时任务(包括已发送和pending中的请求)
  timer_index = options_.io_model->GetReactor()->AddTimerAfter(0, 10, [this]() { this->SetReqTimeoutHandler(); });
  timer_index_vec_.push_back(timer_index);
}

DefaultConnection* ConnComplexConnector::CreateConnection(uint64_t conn_id) {
  connections_active_time_ = xrpc::TimeProvider::GetNowMs();
  return CreateTcpConnection(conn_id);
}
```

Xrpc 检查出来空闲连接会将连接关闭并重连：

```cpp
void ConnComplexConnector::HandleIdleConnection() {
  // 如果请求超时时间很长，send 队列可能还需要等待响应，这个时候不应该关闭重连
  if (send_req_timeout_queue_->Size() > 0) {
    return;
  }

  // 空闲连接，关闭重连
  uint64_t now = xrpc::TimeProvider::GetNowMs();
  if (now - connections_active_time_ >= options_.trans_info->connection_idle_timeout) {
    connection_->DoClose();
    delete connection_;
    connection_ = CreateConnection(0);
  }
}
```

对于请求超时，处理逻辑和 `ConnPoolConnector` 的请求超时完全一致：

- 从请求上下文队列中拿出超时的上下文，如果存在 backup 则触发 backup 请求，否则直接分发异常作为响应。
- 从 Pending 队列中拿出消息，如果存在 backup 则触发 backup 请求，否则直接分发异常作为响应。

ConnComplexConnector 如何发送消息是其核心逻辑之一：

```cpp
int ConnComplexConnector::SendReqMsg(STransportReqMsg* req_msg) {
  // 已经连接，直接发送
  if (GetConnectionCurrentState() == DefaultConnection::ConnectionState::kConnected) {
    return SendReqMsgWhenIsConnected(req_msg);
  }
  
  // 未连接状态下，先连接一下，然后根据连接后的实际状态处理。
  if (GetConnectionCurrentState() == DefaultConnection::ConnectionState::kUnconnected) {
    Connect();
    return SendReqMsgInternal(req_msg);
  }

  // 检测连接中的连接是否超时,如果超时会执行重连操作,然后根据连接后的实际状态处理。
  if (GetConnectionCurrentState() == DefaultConnection::ConnectionState::kConnecting) {
    CheckConnectingTimeout();
    return SendReqMsgInternal(req_msg);
  }

  return -1;
}

int ConnComplexConnector::SendReqMsgWhenIsConnected(STransportReqMsg* req_msg) {
  // 记录请求上下文
  // 请求的 ID 并非由 ConnComplexConnector 进行构建，而是在生成 STransportReqMsg 的应用进行设置
  PushToSendReqTimeoutQueue(req_msg);
  return DoSend(req_msg, connection_);
}

int ConnComplexConnector::SendReqMsgInternal(STransportReqMsg* req_msg) {
  // 如果直接连接成功，发送即可
  if (GetConnectionCurrentState() == DefaultConnection::ConnectionState::kConnected) {
    return SendReqMsgWhenIsConnected(req_msg);
  }
  
  if (GetConnectionCurrentState() == DefaultConnection::ConnectionState::kConnecting) {
    // 连接中，如果连接成功，会执行 NotifySendMsgFunction 连接失败的话，在 pengding 队列中等待超时。
    PushToPendingTimeoutQueue(req_msg);
    return 0;
  }

  uint32_t request_id = req_msg->basic_info->seq_id;
  DispatchException(req_msg, XrpcRetCode::XRPC_CLIENT_CONNECT_ERR, "network unconnected error");
  return -1;
}
```

ConnComplexConnector 对响应的处理是另一个核心逻辑：

- 解析出响应中的请求 id，提取出上下文
- 分发响应任务处理

```cpp
bool ConnComplexConnector::MessageHandleFunction(const ConnectionPtr& conn,
                                                 std::deque<std::any>& rsp_list) {
  for (auto&& rsp_buf : rsp_list) {
    ProtocolPtr rsp_protocol;
    bool ret = options_.trans_info->rsp_decode_function(std::move(rsp_buf), rsp_protocol);
    if (!ret) {
      // 解码异常，Runtime层关闭连接
      return false;
    }

    // 连接复用时，seq_id 在响应信息中
    uint32_t seq_id = 0;
    rsp_protocol->GetRequestId(seq_id);
    STransportReqMsg* msg = PopSendTimeoutQueue(seq_id);

    if (msg) {
      // 构造STransportRspMsg，派发响应
      STransportRspMsg rsp_msg;
      rsp_msg.msg = std::move(rsp_protocol);
      DispatchResponse(msg, std::move(rsp_msg));
    }
  }
  return true;
}
```

对于连接网络事件所触发的保活事件，只需要更新以下活跃时间即可：

```cpp
void ActiveTimeUpdate(ConnectionPtr conn) {
  connections_active_time_ = TimeProvider::GetNowMs();
}
```

## FutureConnectionHandler

Connector 的连接回调事件均是由 `FutureConnectionHandler` 类定义，该类处理回调时主要以来：

- [TransInfo](#transinfo) 中定义的方法。
- 类中的函数变量。

这是提供的事件处理：

```cpp
class FutureConnectionHandler : public ConnectionHandler {
 public:
  explicit FutureConnectionHandler(TransInfo* trans_info);

  // 消息协议的完整性检测接口
  int MessageCheck(const ConnectionPtr&, NoncontiguousBuffer&, std::deque<std::any>&) override {
    return trans_info_->checker_function(conn, in, out);
  }

  // 连接建立成功后的处理接口
  void ConnectionEstablished(const ConnectionPtr&) override {
    trans_info_->conn_establish_function(conn);
  }

  // 连接关闭后的处理接口
  void ConnectionClosed(const ConnectionPtr&) override {
    trans_info_->conn_close_function(conn);
  }

  // 消息协议处理接口
  bool MessageHandle(const ConnectionPtr&, std::deque<std::any>&) override {
    return message_handle_func_(conn, data);
  }

  // 连接相关的资源清理接口
  void ConnectionClean(const ConnectionPtr&) override {
    clean_func_(conn);
  }

  // 连接保活的时间更新接口
  void ConnectionTimeUpdate(const ConnectionPtr&) override {
    time_update_func_(conn);
  }

  // 请求建立成功后的通知消息发送接口
  void NotifySendMessage(const ConnectionPtr&) override {
    notify_msg_send_func_(conn);
  }
};
```

## IO Handler

## TransportMessage

Transport 对外暴露的暴露的发送接口参数是 `STransportReqMsg`，响应数据是 `STransportRspMsg`，这两个结构本质上都是 `TransportMessage`：

```cpp
using STransportReqMsg = TransportMessage;
using STransportRspMsg = TransportMessage;
```

因此其结构是重要的，STransportReqMsg 里包含了一些重要的信息，这个结构也作为请求的上下文存在。

```cpp
struct TransportMessage {
  // 记录 Transport 的基本信息，例如使用的连接 ID、连接类型、fd、对端地址 等。
  // 这里面的信息使用方需要填一部分，另一部分框架会自动填
  // 用户主要填请求的目标、超时等信息，例如 addr port timeout 等
  BasicInfo*  basic_info = nullptr;

  // 扩展信息，使用方法通过该结构体提供一些辅助能力
  // 例如触发应用层 future 回调的 promise，记录相关处理的分发信息 等
  ExtendInfo* extend_info = nullptr;

  // 应用层定义的消息结构体对象，响应会将消息解析并结构化后放在 msg 中
  std::any msg = nullptr;

  // msg 消息的二进制底层数据，发送数据直接用它
  // message.buffer = TransportMessage->send_data;
  // conn->Send(std::move(message))
  NoncontiguousBuffer send_data;
};

struct ExtendInfo {
  ProtocolMessageMetadata metadata{};
  ServerExtendInfo server_extend_info;
  ClientExtendInfo client_extend_info;
};

struct ClientExtendInfo {
  // 保存请求回包的 promise
  void* promise = nullptr;

  // 触发 backup 处理的 promise
  void* backup_promise = nullptr;
  RetryInfo* retry_info = nullptr;

  // 处理分发信息
  ThreadModelDispatchInfo* dispatch_info = nullptr;
};

struct ThreadModelDispatchInfo {
  // 请求发起的thread_model id
  int src_thread_model_id = -1;

  // 请求发起线程id
  int src_thread_id = -1;

  // 应答处理的目的线程id
  int dst_thread_key = -1;
};

struct BasicInfo {
  // 标识
  uint64_t flag = 0;

  // 连接唯一id
  uint64_t connection_id = 0;

  // 连接类型
  ConnectionType connection_type;

  // fd
  int32_t fd = -1;

  // 流唯一id
  uint32_t stream_id = 0;

  // req唯一id，标识请求上下文
  uint32_t seq_id = 0;

  // 请求的超时时间
  uint32_t timeout = UINT32_MAX;

  // 请求开始的时间戳
  int64_t begin_timestamp = 0;

  // 请求结束的时间戳
  int64_t end_timestamp = 0;

  // pipeline的数量
  uint32_t pipeline_count = 1;

  // 调用类型
  RpcCallType call_type{RpcCallType::UNARY_CALL};

  // ip/port相关信息
  NodeAddr addr;
};
```

## Options

### FutureTransport::Options

```cpp
class FutureTransport : public ClientTransport {
 public:
  struct Options {
    // FutureTransport 绑定到一个 ThreadModel 上，该 ThreadModel 负责该 Transport 的所有任务
    ThreadModel* thread_model;

    // Transport 的深度配置，包括连接数、连接类型、网络包分发策略、网络事件处理等
    TransInfo trans_info;

    // Transport 的名称
    std::string transport_name;
  };
};
```

### TransInfo

```cpp
struct TransInfo {
 public:
  // 请求派发到哪个io线程发送，业务可自定义注册
  using ReqDispatchFunction = std::function<uint16_t(const uint16_t io_thread_num)>;

  // 应答派发到handle线程策略指定，业务可自定义注册
  using RspDispatchFunction = std::function<void(Task* task)>;

  // 应答解码
  using RspDecodeFunction = std::function<bool(std::any&& in, ProtocolPtr& out)>;

  // 连接类型
  ConnectionType conn_type;

  // 请求是否要求使用连接复用模式
  bool is_complex_conn = true;

  // 连接允许的请求的最大包大小
  uint32_t max_packet_size = 10000000;

  // 接收数据时，每次分配内存buffer的大小
  uint32_t recv_buffer_size = 8192;

  // 合并发送数据的大小
  uint32_t merge_send_data_size = 1024;

  // 连接池模式下最大活跃连接数
  uint32_t max_conn_num = 64;

  // 空闲连接超时
  uint32_t connection_idle_timeout = 50000;

  // 连接建立用户回调
  ConnectionEstablishFunction conn_establish_function = nullptr;

  // 连接关闭用户回调
  ConnectionCloseFunction conn_close_function = nullptr;

  // 数据包完整性校验操作
  ProtocalCheckerFunction checker_function = nullptr;

  // 请求发送成功后用户回调
  MessageWriteDoneFunction msg_writedone_function = nullptr;

  // 回包解码
  RspDecodeFunction rsp_decode_function = nullptr;

  // 请求包发到哪个io线程策略指定，业务可自定义注册
  ReqDispatchFunction req_dispatch_function = nullptr;

  // 应答派发到handle线程策略指定，业务可自定义注册
  RspDispatchFunction rsp_dispatch_function = nullptr;

  // redis鉴权配置信息
  RedisClientConf redis_conf;

  // Set SSL/TLS options and context for client.
#ifdef BUILD_INCLUDE_SSL
  // Option of ssl context: certificate and key and ciphers were stored in.
  ssl::SslClientSslOptionsPtr ssl_options{nullptr};
  // Context of ssl
  ssl::SslContextPtr ssl_ctx{nullptr};
#endif

  // 连接上传输应用数据协议名称, 例如: xrpc, 当前用于流式场景
  std::string codec_name{};
};
```
