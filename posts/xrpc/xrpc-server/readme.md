# XRPC Server

<!-- TOC -->

- [XRPC Server](#xrpc-server)
    - [Overview](#overview)
    - [Quick Start](#quick-start)
    - [UML Class Diagram](#uml-class-diagram)
    - [Sequence Diagram](#sequence-diagram)
        - [Server Start Diagram](#server-start-diagram)
        - [Process Request Diagram](#process-request-diagram)
        - [Async Response Diagram](#async-response-diagram)
    - [XrpcServer](#xrpcserver)
        - [XrpcServer Initial](#xrpcserver-initial)
        - [RegistryService](#registryservice)
        - [XrpcServer Start](#xrpcserver-start)
    - [ServiceAdapter](#serviceadapter)
        - [ServiceAdapter SetService](#serviceadapter-setservice)
        - [ServiceAdapter Listen](#serviceadapter-listen)
        - [HandleAnyMessage](#handleanymessage)
    - [Service](#service)
        - [ServiceImpl](#serviceimpl)
        - [RpcServiceImpl](#rpcserviceimpl)
        - [ConcreteRpcService](#concreterpcservice)
        - [HttpService](#httpservice)
    - [UnaryServiceHandler](#unaryservicehandler)
    - [RpcMethodHandler](#rpcmethodhandler)
    - [ServerContext](#servercontext)
        - [Async Response](#async-response)

<!-- /TOC -->

## Overview

Xrpc Server 进一步封装了监听连接，处理连接的接口，一个 Xrpc Server 可以由一个或多个 Service 组成。

Xrpc Server 已经提供了多种类型的 Service 的实现（例如 http service, rpc service），也可以在此基础上扩展其他类型的 Service。

开发人员决定使用什么 Service 后，就可以在此基础上实现各个 Service 的逻辑处理函数，并决定 Service 收到请求后如何去分发这些请求到对应的逻辑处理函数。

## Quick Start

通过我们实现一个自定义的 Echo Service 来快速理解 Xrpc Server 的工作机制。

其中最重要的是构建 ServiceAdapter，以及处理请求和响应的 Service。

其次，我们需要一个 ServerCodec 去处理沾包分包问题，Codec 并非本节的重点，并且 Echo 的 Codec 非常简单，这里会提供一个简单的实现。

```cpp
#include <iostream>
#include <memory>
#include <string>
#include <thread>

#include "xrpc/server/service.h"
#include "xrpc/server/service_adapter.h"
#include "xrpc/common/config/xrpc_config.h"
#include "xrpc/common/future/future_utility.h"
#include "xrpc/common/xrpc_plugin.h"

class EchoServerCodec : public xrpc::ServerCodec {
 public:
  EchoServerCodec() = default;
  ~EchoServerCodec() override = default;
  std::string Name() const override { return "echo"; }

  // 校验 Packet 完整性，处理沾包分包
  int ZeroCopyCheck(const xrpc::ConnectionPtr& conn,
                    xrpc::NoncontiguousBuffer& in,
                    std::deque<std::any>& out) override {
    std::cout << "========== Check ==========" << std::endl;
    out.push_back(in);
    in.Clear();
    return xrpc::PacketChecker::PACKET_FULL;
  }
};

class EchoService : public xrpc::Service {
 public:
  EchoService() {}
  ~EchoService() {}

  // 将数据原封不动返回
  void HandleTransportMessage(xrpc::STransportReqMsg *recv,
                              xrpc::STransportRspMsg **send) override {
    std::cout << "========== HandleTransportMessage ==========" << std::endl;
    *send = new xrpc::STransportRspMsg();
    (*send)->basic_info = recv->basic_info;
    (*send)->send_data = std::any_cast<xrpc::NoncontiguousBuffer&>(recv->msg);
  }
};

void Start() {
  // Register Codec
  xrpc::ServerCodecPtr codec(new EchoServerCodec());
  xrpc::XrpcPlugin::GetInstance()->RegisterServerCodec(codec);

  // Service
  xrpc::ServicePtr echo_service(new EchoService());

  // ServiceAdapter Options
  xrpc::ServiceAdapterOption option;
  option.socket_type = "net";
  option.network = "tcp";
  option.ip = "0.0.0.0";
  option.is_ipv6 = false;
  option.port = 8899;
  option.protocol = "echo";
  option.max_packet_size = 10000000;
  option.recv_buffer_size = 8192;
  option.merge_send_data_size = 8192;

  xrpc::ServiceAdapter adapter(option);
  adapter.SetService(echo_service);
  adapter.Listen();

  // sleep
  auto promise = xrpc::Promise<bool>();
  auto fut = promise.get_future();
  fut.Wait();
}

int main() {
  xrpc::XrpcConfig::GetInstance()->Init("test_server.yaml");
  xrpc::XrpcPlugin::GetInstance()->InitThreadModel();
  Start();
  xrpc::XrpcPlugin::GetInstance()->DestroyThreadModel();
}
```

## UML Class Diagram

```mermaid
classDiagram

XrpcServer --> ServiceAdapter
ServiceAdapter --> Service
Service <|-- HttpService
Service <|-- ServiceImpl
ServiceImpl <|-- RpcServiceImpl
RpcServiceImpl <|-- ConcreteRpcService

class XrpcServer {
  +ServerConfig server_config_
  +map<std::string, ServiceAdapterPtr> service_adapters_
  +AdminServicePtr admin_service_
  +Start()
  +WaitForShutdown()
  +RegistryService(service_name, service)
  +GetAdminService() AdminServicePtr
  +Destroy()
}

class ServiceAdapter {
  +ServiceAdapterOption option_
  +ServerTransport transport_
  +ThreadModel threadmodel_
  +ServicePtr service_
  +ServerCodecPtr server_codec_
  +ServiceAdapter(options)
  +Destroy()
  +GetServiceName() string
  +GetProtocol() string
  +SetService(service)
  +GetService() ServicePtr
  +GetServerCodec() ServerCodecPtr
  +HandleAnyMessage(conn, msg)
  +SendMsg(msg)
  +Listen()
  +SubmitHandleTask(task)
}

class Service {
  +ServiceAdapter* adapter_
  +HandleRequestDispatcherFunction dispatcher_func_
  +std::unordered_map<std::string, RpcServiceMetho
  +std::unordered_map<std::string, NonRpcServiceMetho
  +AcceptConnectionFunction accept_connection_function_
  +ConnectionEstablishFunction connection_establish_function_
  +ConnectionCloseFunction connection_close_function_
  +ProtocalCheckerFunction protocol_checker_function_
  +MessageHandleFunction message_handle_function_
  +MessageWriteDoneFunction message_writedone_function_
  +HandleTransportMessage(recv, send) virtual
  +AddRpcServiceMethod(method)
  +AddNonRpcServiceMethod(method)
  +SetHandleRequestDispatcherFunction(function)
  +SetAcceptConnectionFunction(function)
  +SetConnectionEstablishFunction(function)
  +SetConnectionCloseFunction(function)
  +SetProtocalCheckerFunction(function)
  +SetMessageHandleFunction(function)
  +SetMessageWriteDoneFunction(function)
}

class ServiceImpl {
  +UnaryServiceHandler unary_service_handler_
  +StreamServiceHandler stream_service_handler_
  +SendUnaryResponse(context, rsp, send) virtual
  +HandleTransportMessage(recv, send)
  +Dispatch(context, req, rsp) virtual
  +DispatchStream(context) virtual
  +HandleFlowController(context);
  +HandleTimeout(context)
}

class RpcServiceImpl {
  +Dispatch(context, req, rsp)
  +DispatchStream(context)
  +SendUnaryResponse(context, rsp, send)
}

class ConcreteRpcService {
  
}

class HttpService {
  +FilterController filter_controller_
  +HandleTransportMessage(recv, send)
  +SetRoutes(function)
}
```

ServerContext 是一个独立的类，是 Server 接收到请求后为其创建的上下文，每个请求都会有一个独立的 ServerContext，并在 Server 响应完毕后销毁。

这里为 ServerContext 进行单独呈现：

```mermaid
classDiagram

class ServerContext {
  +Status status_
  +ProtocolPtr req_msg_
  +ProtocolPtr rsp_msg_
  +BasicInfoPtr basic_info_
  +SendUnaryResponse(status, biz_rsp)
  +SendUnaryResponse(status)
  +SendResponse(buff)
  +SetRequestMsg(req)
  +SetResponseMsg(rsp)
  +SetResponse(is_response)
  +SetRspCompressType(compress_type)
  +SetRspEncodeType(encode_type)
  +SetStatus(status)
  +GetRequestMsg() ProtocolPtr
  +GetResponseMsg() ProtocolPtr
  +IsResponse() bool
  +GetStatus() Status
}
```

## Sequence Diagram

下面显示几种场景的时序图。

### Server Start Diagram

```mermaid
sequenceDiagram
autonumber

participant main as Main
participant xrpc_app as XrpcApp
participant xrpc_server as XrpcServer
participant service_adapter as ServicAdapter
participant concrete_service as ConcreteService

main ->> xrpc_app: app.Main()
xrpc_app ->> xrpc_app: 框架相关初始化
xrpc_app -->> main: Return

rect rgba(0, 255, 255, .1)
  main ->> xrpc_app: app.Wait()

  rect rgba(255, 0, 255, .1)
    xrpc_app ->> xrpc_server: 创建 Server 实例
    xrpc_server ->> service_adapter: 根据配置文件的 service 配置创建多个 service_adapter
    service_adapter -->> xrpc_server: 返回 service_adapter 实例
    xrpc_server -->> xrpc_app: 返回 Server 实例
  end

  rect rgba(255, 0, 0, .1)
    xrpc_app ->> concrete_service: 创建 Service 实例
    concrete_service ->> xrpc_app: 返回 Service 实例
    xrpc_app ->> xrpc_server: Server.RegistryService 注册 Service
    xrpc_server ->> service_adapter: ServiceAdapter.SetService 设置 Service
    service_adapter -->> xrpc_server: Return
    xrpc_server -->> xrpc_app: Return
  end

  rect rgba(0, 0, 255, .1)
    xrpc_app ->> xrpc_server: server.Start()
    loop 遍历 service_adapter
      xrpc_server ->> service_adapter: ServiceAdapter.Listen()
      service_adapter -->> xrpc_server: Return
    end
    xrpc_server -->> xrpc_app: Return
  end
  xrpc_app ->> xrpc_server: server.WaitForShutdown()
  loop 满足 server 退出条件
    xrpc_server ->> xrpc_server: 运行 terminate_function 检查退出条件
  end
  xrpc_server --> xrpc_app: Return
  xrpc_app ->> xrpc_app: Destory()
  xrpc_app -->> main: Return
end
```

### Process Request Diagram

这里的时序图展示了 Reactor 感知到请求，并交给 ServiceAdapter 进行处理的过程：

```mermaid
sequenceDiagram
autonumber

participant io_thread as IO Thread
participant handl_thread as Handle Thread
participant server_transport as ServerTransport
participant service_adapter as ServicAdapter
participant concrete_service as ConcreteService

io_thread ->> io_thread: reactor 感知到可读事件
io_thread ->> io_thread: 根据 BindInfo.check_function 进行数据完整行检查甚至解析数据

rect rgba(255, 255, 0, .2)
  io_thread ->> service_adapter: HandleAnyMessage 处理收到的数据
  service_adapter ->> service_adapter: 构造消息处理 Task
  service_adapter ->> handl_thread: 提交至 Handle Thread 进行处理
  handl_thread -->> service_adapter: 返回，任务可能不会立即处理
  service_adapter -->> io_thread: 返回
end

rect rgba(0, 255, 255, .2)
  handl_thread ->> concrete_service: Service.HandleTransportMessage 将消息交给 Service 进行处理
  concrete_service ->> concrete_service: 分发消息至对应的 HTTP/RPC Handler 进行处理
  concrete_service -->> handl_thread: 返回处理的结果

  alt 如果需要立即返回数据
    handl_thread ->> handl_thread: 返回数据，该步骤会使用 ServerTransport 向 IO Thread 提交任务
  end
end
```

### Async Response Diagram

在上述流程中展现了接收到了数据如何处理，并如何进行同步响应，那对于异步响应在 xrpc 中是如何处理的呢？

1. 在对请求处理时，需要设置 `context->SetResponse(false)`
1. 需要响应数据时，使用 `ServerContext::SendUnaryResponse()` 方法。

这一部分很简单，不用额外再用时序图来表示了，可以参考 [Async Response](#async-response) 部分。

## XrpcServer

XrpcServer 类管理了 Xrpc App 的 Server 启动和关闭，它可以包含了很多 Service，并且每个 Service 的都用 [ServiceAdapter](#serviceadapter) 进行表示。

### XrpcServer Initial

在 Xrpc App 中包含了一个 Xrpc Server，由 Xrpc App 对 Xrpc Server 进行初始化：

```cpp
void XrpcApp::Wait() {
  InitializeRuntime();

  // DestoryRuntime 会组塞
  DestoryRuntime();
}

void XrpcApp::InitializeRuntime() {
  // ...

  // 初始化服务端
  InitXrpcServer();

  // ...

  // 由应用层进行相关初始化，主要会进行 Service 的构建和注册。
  int ret = Initialize();

  // server_ 开始监听
  server_->Start();
}

void XrpcApp::InitXrpcServer() {
  server_ = std::make_shared<XrpcServer>(XrpcConfig::GetInstance()->GetServerConfig());
}

void XrpcApp::DestoryRuntime() {
  server_->WaitForShutdown();
  Destory();

  // ...
}
```

Xrpc Server 初始化主要是根据 Xrpc Config 进行 ServiceAdapter 的初始化，这主要是一些网络配置相关的初始化。

```cpp
XrpcServer::XrpcServer(const ServerConfig &server_config) : server_config_(server_config) {
  InitializeServiceAdapter();
}

void XrpcServer::InitializeServiceAdapter() {
  // 根据框架配置中 server 配置中的 service 配置信息，初始化 service 的相关信息
  for (const auto& config : server_config_.services_config) {
    BuildServiceAdapter(config);
  }
}

ServiceAdapterPtr XrpcServer::BuildServiceAdapter(const ServiceConfig& config) {
  // 根据配置文件得到 ServiceAdapter 的配置
  ServiceAdapterOption option;
  BuildServiceAdapterOption(config, option);

  ServiceAdapterPtr service_adapter(new ServiceAdapter(option));
  service_adapters_[config.service_name] = service_adapter;
  return service_adapter;
}
```

### RegistryService

虽然 Xrpc Server 初始化时，已经将 ServiceAdapter 进行初始化了，但是 ServiceAdapter 还没有对网络事件进行具体处理 Service。为了让 ServiceAdapter 拥有一个进行消息处理的 Service，需要将 Service 初始化后通过 RegistryService 进行注册：

```cpp
void XrpcServer::RegistryService(const std::string &service_name, ServicePtr &service) {
  auto service_adapter_it = service_adapters_.find(service_name);
  if (service_adapter_it == service_adapters_.end()) {
    XRPC_LOG_ERROR("service_name:" << service_name << " not found.");
    XRPC_ASSERT(service_adapter_it != service_adapters_.end());
  }

  // 设置 ServiceAdapter 的 Service
  service_adapter_it->second->SetService(service);
  service->SetAdapter(service_adapter_it->second.get());
}
```

### XrpcServer Start

在一切准备就绪后，调用 Xrpc Server 的 Start 方法进行监听，等待网络事件触发：

```cpp
void XrpcServer::Start() {
  for (const auto &iter : service_adapters_) {
    iter.second->Listen();
  }
}
```

在 Start 后，应用层应该通过 `WaitForShutdown` 等待 Server 结束：

```cpp
void XrpcServer::WaitForShutdown() {
  // 等待服务停止
  while (!terminate_) {
    // default thread sleep
    std::this_thread::sleep_for(std::chrono::milliseconds(100));

    // 周期调用 terminate_function_ 检查是否满足停止 Server 的条件
    if (terminate_function_) {
      terminate_ = terminate_function_();
    }
  }
}
```

## ServiceAdapter

Xrpc Config 中配置的 Service 都由 ServiceAdapter 进行管理和设置，也包含了对相关网络事件回调的设置：

- ServiceAdapter 包含一个 ServerTransport，用于对网络进行监听、网络事件回调配置。
- ServiceAdapter 包含一个 [Service](#service) 对象，Service 对象封装了网络事件的回调具体逻辑。

ServiceAdapter 主要是记录配置文件，以及记录使用的线程池。

ServiceAdapter 最重要的初始化方法是 SetService。

### ServiceAdapter SetService

SetService 用于向 ServiceAdapter 注册 Service 实例，本质上主要是进行 ServerTransport 的 BindInfo 设置，包括监听的端口、回调等：

```cpp
void ServiceAdapter::SetService(const ServicePtr& service) {
  service_ = service;

  xrpc::BindInfo bind_info;
  bind_info.socket_type = option_.socket_type;
  bind_info.ip = option_.ip;
  bind_info.is_ipv6 = option_.is_ipv6;
  bind_info.port = option_.port;
  bind_info.network = option_.network;
  bind_info.unix_path = option_.unix_path;
  bind_info.protocol = option_.protocol;
  bind_info.idle_time = option_.idle_time;
  bind_info.max_conn_num = option_.max_conn_num;
  bind_info.max_packet_size = option_.max_packet_size;
  bind_info.recv_buffer_size = option_.recv_buffer_size;
  bind_info.merge_send_data_size = option_.merge_send_data_size;
  bind_info.accept_thread_num = option_.accept_thread_num;

  // 下面四个函数在 HTTP Service / RPC Service 中，默认情况下都没有使用，除非进行人为甚至
  bind_info.accept_function = service_->GetAcceptConnectionFunction();
  bind_info.conn_establish_function = service_->GetConnectionEstablishFunction();
  bind_info.conn_close_function = service_->GetConnectionCloseFunction();
  bind_info.msg_writedone_function = service_->GetMessageWriteDoneFunction();

  // server_codec_ 进行 Packet 检测甚至解码
  bind_info.checker_function = std::bind(&ServerCodec::ZeroCopyCheck, server_codec_.get(),
                                         _1, _2, _3);

  // HandleAnyMessage 进行消息处理，主要是构造处理任务，提交至 Handle 线程池进行消息处理
  bind_info.msg_handle_function = std::bind(&ServiceAdapter::HandleAnyMessage, this,
                                            _1, _2);

  xrpc::ServerTransportImpl::Options options;
  options.thread_model_ = threadmodel_;
  transport_ = std::make_unique<ServerTransportImpl>(options);

  XRPC_ASSERT(transport_);
  transport_->Bind(bind_info);
}
```

### ServiceAdapter Listen

Listen 会让 ServerTransport 进行监听，相应网络事件触发后，由 BindInfo 配置的回调进行处理。

```cpp
void ServiceAdapter::Listen() {
  transport_->Listen();
}
```

### HandleAnyMessage

ServiceAdapter 提供了默认了对请求数据进行处理的方法，即 HandleAnyMessage，对于大多数 Service 都会使用该方法进行处理，例如 HTTP Service、XRPC Service。

HandleAnyMessage 回调是在 IO 线程触发的，为了不组塞 IO 线程，该函数会构建 task 并提交至 Handle 线程进行处理。

HandleAnyMessage 本质上会将请求的数据交给 Service 的 HandleTransportMessage进行处理：

```cpp
bool ServiceAdapter::HandleAnyMessage(const ConnectionPtr& conn, std::deque<std::any>& msg) {
  // msg 是经过 checker_function 进行处理后的输出
  // msg 可能是解码的结构体，也可能是未解码的二进制数据，具体情况需要依赖 server_codec 的实现
  // http server codec 的 checker 会解码 这里拿到的是解码后的 http 结构体
  // rpc server codec 的 checker 不会解码 这里拿到的是底层二进制数据 并在 service HandleTransportMessage 中进行解码
  for (auto it = msg.begin(); it != msg.end(); ++it) {
    STransportReqMsg* req_msg = new STransportReqMsg();
    req_msg->basic_info = object_pool::GetRefCounted<BasicInfo>();
    req_msg->basic_info->connection_id = conn->GetConnId();
    req_msg->basic_info->connection_type = conn->GetConnType();
    req_msg->basic_info->fd = conn->GetFd();
    req_msg->basic_info->begin_timestamp = xrpc::TimeProvider::GetNowMs();
    req_msg->basic_info->addr.ip = conn->GetPeerIp();
    req_msg->basic_info->addr.port = conn->GetPeerPort();
    req_msg->msg = std::move(*it);

    Task* task = new Task;
    task->task_type = TaskType::TRANSPORT_REQUEST;
    task->task = req_msg;
    task->handler = [this](Task* task) {
      STransportReqMsg* req_msg = static_cast<STransportReqMsg*>(task->task);
      STransportRspMsg* send = nullptr;

      // 应用层处理
      this->service_->HandleTransportMessage(req_msg, &send);
      if (send) {
        this->transport_->SendMsg(send);
      }
    };

    // 如果用户配置了回调, 则根据用户回调获取线程id
    HandleRequestDispatcherFunction& dispatcher_ = service_->GetHandleRequestDispatcherFunction();
    if (dispatcher_) {
      task->dst_thread_key = dispatcher_(req_msg);
    }

    task->group_id = threadmodel_->GetThreadModelId();
    threadmodel_->SubmitHandleTask(task);
  }

  return true;
}
```

## Service

Xrpc 的 Service 由 [ServiceAdapter](#serviceadapter) 进行维护。

Service 屏蔽了 Server 创建连接、关闭连接等等业务不需要关心的事件（当然也可以选择去关心），其核心是：

- 提供了 `HandleTransportMessage` 方法对请求进行处理。
- 提供了 `SendUnaryResponse` 方法，针对同步模式进行响应。

### ServiceImpl

ServiceImpl 是 RpcService 的父类，主要提供了流控和 RPC 消息处理的入口。

#### HandleTransportMessage

ServiceImpl::HandleTransportMessage 是 RpcService 和 NonRpcService 的统一消息处理入口：

```cpp
void ServiceImpl::HandleTransportMessage(STransportReqMsg* recv, STransportRspMsg** send) {
  // 尝试处理流式数据, 如果不是流式数据, 则走unary逻辑
  if (recv->basic_info->call_type == RpcCallType::BIDI_STREAM_CALL) {
    stream_service_handler_->HandleMessage(recv, std::move(recv->extend_info->metadata));
    return;
  }

  // 默认走unary逻辑
  unary_service_handler_->HandleMessage(recv, send);
}
```

`unary_service_handler_->HandleMessage()` 由 [UnaryServiceHandler](#unaryservicehandler) 进行处理，其中包括了上下文创建、Filter 执行、限流等处理，最重要的是分发请求到对应的 RPC Handler 执行。在 [UnaryServiceHandler](#unaryservicehandler) 中，最终会使用 [RpcServiceImpl](#rpcserviceimpl) 的 Dispatch 函数进行分发请求处理。

#### SendUnaryResponse

ServiceImpl::SendUnaryResponse 是 RpcService 和 NonRpcService 的统一消息（同步）回复函数：

```cpp
void ServiceImpl::SendUnaryResponse(const ServerContextPtr& context, ProtocolPtr& rsp,
                                    STransportRspMsg** send) {
  NoncontiguousBuffer send_data;

  // 将数据序列化为二进制数据
  adapter_->GetServerCodec()->ZeroCopyEncode(context, context->GetResponseMsg(), send_data);

  // 构造响应 Message
  *send = new STransportRspMsg();
  (*send)->basic_info = context->GetTransportBasicInfo();
  (*send)->send_data = std::move(send_data);
}
```

很明显，该函数并非进行实际的 IO 调用，而是构造一个 STransportRspMsg* send 消息体，该消息的实际发送是在 ServiceAdapter 的 HandleAnyMessage 构造的 task 中：

```cpp
bool ServiceAdapter::HandleAnyMessage(const ConnectionPtr& conn, std::deque<std::any>& msg) {
  Task* task = new Task;
  task->handler = [this](Task* task) {
    this->service_->HandleTransportMessage(req_msg, &send);

    // send 数据已经构造，则发送数据
    if (send) {
      this->transport_->SendMsg(send);
    }
  };
  
  threadmodel_->SubmitHandleTask(task);

  return true;
}
```

该函数请参考 [HandleAnyMessage](#handleanymessage)。

### RpcServiceImpl

RpcServiceImpl 是 RpcService 实现类，主要是实现如何将请求分发给对应的 RPC Handler 函数进行处理。

分发通过 Dispatch 进行实现，由 [UnaryServiceHandler](#unaryservicehandler) 调用：

```cpp
void RpcServiceImpl::Dispatch(const ServerContextPtr& context, const ProtocolPtr& req,
                              ProtocolPtr& rsp) {
  // rpc_service_methods 由 RpcServiceImpl 子类初始化时进行 methods 的注册
  const auto& rpc_service_methods = GeXRPCServiceMethod();

  // 根据 function name 找到 RPC Handler
  // name e.g. /xrpc.test.helloworld.Greeter/SayHello
  auto it = rpc_service_methods.find(context->GetFuncName());
  if (it == rpc_service_methods.end()) {
    context->GetStatus().SetFrameworkRetCode(xrpc::codec::ServerRetCode::NOT_FUN_ERROR);
    context->GetStatus().SetErrorMessage("not found");
    return;
  }

  NoncontiguousBuffer response_body;
  RpcMethodHandlerInterface* method_handler = it->second->GeXRPCMethodHandler();
  method_handler->Execute(context, req->GetNonContiguousProtocolBody(), response_body);

  // 同步响应，设置响应 Body
  if (context->IsResponse()) {
    rsp->SetNonContiguousProtocolBody(std::move(response_body));
  }

  return;
}
```

### ConcreteRpcService

ConcreteRpcService 是 RpcServiceImpl 的实现类，通常由 protobuf 编译生成，在该类中会进行 RPC Handler 的注册（通过 `AddRpcServiceMethod`）。

如果存在这样一个 protobuf：

```proto
syntax = "proto3";
  
package xrpc.test.helloworld;
  
service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply) {}
}

message HelloRequest {
   string req_msg = 1;
}
  
message HelloReply {
   string rsp_msg = 1;
}
```

在 Xrpc 编译后会转换成这样一个 ConcreteRpcService：

```cpp
//
// This file was generated by xrpc_cpp_plugin which is a self-defined pb compiler plugin, do not edit it!!!
// All rights reserved by Tencent Corporation
//

#include "test/helloworld/greeter.xrpc.pb.h"

#include <functional>
#include "xrpc/server/rpc_method_handler.h"
#include "xrpc/server/stream_rpc_method_handler.h"

namespace xrpc {
namespace test {
namespace helloworld {

static const char* Greeter_method_names[] = {
  "/xrpc.test.helloworld.Greeter/SayHello",
};

Greeter::Greeter() {
  auto rpc_func = std::bind(&Greeter::SayHello, this, std::placeholders::_1, std::placeholders::_2, std::placeholders::_3)
  auto rpc_handler = new xrpc::RpcMethodHandler<xrpc::test::helloworld::HelloRequest,
                                                xrpc::test::helloworld::HelloReply>(rpc_func);
  auto method = new xrpc::RpcServiceMethod(Greeter_method_names[0],
                                           xrpc::MethodType::UNARY,
                                           rpc_handler);
  AddRpcServiceMethod(method);
}

Greeter::~Greeter() {}

// 由用户进行重写
xrpc::Status Greeter::SayHello(xrpc::ServerContextPtr context,
                               const xrpc::test::helloworld::HelloRequest* request,
                               xrpc::test::helloworld::HelloReply* response) {
  return xrpc::Status(-1, "");
}
```

最终会由用户继承 ConcreteRpcService 并 overwrite 其中的 RPC Handler，例如：

```cpp
class GreeterServiceImpl final : public xrpc::test::helloworld::Greeter {
 public:
  GreeterServiceImpl();
  ~GreeterServiceImpl();
  xrpc::Status SayHello(xrpc::ServerContextPtr context,
                        const xrpc::test::helloworld::HelloRequest* request,
                        xrpc::test::helloworld::HelloReply* reply) override {
    return xrpc::Status(-1, "");
  }
};
```

### HttpService

HttpService 直接继承于 Service：

- 提供了将 Path 和处理函数绑定的方法。
- 消息处理入口 `HandleTransportMessage`，用于根据请求 Path 分发至绑定的 Handler 进行处理。

```cpp
void HttpService::HandleTransportMessage(STransportReqMsg* recv, STransportRspMsg** send) {
  ServerContextPtr context = MakeRefCounted<ServerContext>(*recv);

  // http 这里拿到的 msg 是已经解码后的
  http::HttpRequestPtr& http_req = std::any_cast<http::HttpRequestPtr&>(recv->msg);
  http::HttpReply& http_rsp = static_cast<HttpResponseProtocol*>(context->GetResponseMsg().get())->http_rsp;

  // Filters 处理
  GetFilterController().RunMessageServerFilters(FilterPoint::SERVER_POST_RECV_MSG, context);

  // 分发至 Handler 处理
  auto status = Dispatch(context, http_req, http_rsp);

  context->SetStatus(status);
  if (context->IsResponse()) {
    // Filters 处理
    GetFilterController().RunMessageServerFilters(FilterPoint::SERVER_PRE_SEND_MSG, context);

    // 将响应数据序列化
    *send = new STransportRspMsg();
    (*send)->basic_info = context->GetTransportBasicInfo();
    http_rsp.SerializeToString((*send)->send_data);
  }
}
```

通过 Dispatch 函数将请求分发至相应的 Handler 处理：

```cpp
Status HttpService::Dispatch(ServerContextPtr& context, http::HttpRequestPtr& req,
                             http::HttpReply& rsp) {
  return routes_.Handle(req->GetRouteUrl(), context, req, rsp);
}
```

## UnaryServiceHandler

进一步封装了如何处理请求消息，包括：

- 生成 Server 上下文
- 执行过滤器
- 流量控制
- 超时判断
- 分发请求到对应的 RPC Handler 函数处理

下面省略对异常的判断：

```cpp
void HandleMessage(STransportReqMsg* recv, STransportRspMsg** send) {
    auto* adapter = service_impl_->GetAdapter();

    // 创建上下文
    ServerContextPtr context = MakeRefCounted<ServerContext>(*recv);
    context->SetAdapter(adapter);

    // 上下文保存解码后的请求对象，实际是智能指针
    context->SetRequestMsg(adapter->GetServerCodec()->CreateRequestObject());
    context->SetResponseMsg(adapter->GetServerCodec()->CreateResponseObject());

    // 协议解码
    adapter->GetServerCodec()->ZeroCopyDecode(context, std::move(recv->msg), context->GetRequestMsg());

    // 设置当前请求真正的超时时间，协议所带的链路超时和所属service的消息超时两者之间的最小值
    context->SetRealTimeout();

    // 接收请求消息埋点，
    filter_controller_.RunMessageServerFilters(FilterPoint::SERVER_POST_RECV_MSG, context);

    // 流量控制
    service_impl_->HandleFlowController(context);

    // 超时判断
    service_impl_->HandleTimeout(context);

    // 请求消息分发处理
    service_impl_->Dispatch(context, context->GetRequestMsg(), context->GetResponseMsg());

    // 回包
    if (context->IsResponse()) {
      service_impl_->SendUnaryResponse(context, context->GetResponseMsg(), send);
    }
  }
```

上述对于同步调用的回包 `service_impl_->SendUnaryResponse(context, context->GetResponseMsg(), sned)` 并不会立即发送数据，而是在 ServiceAdapter 的 HandleAnyMessage 中进行实际的响应发送。对于这一点，请参考 [SendUnaryResponse](#sendunaryresponse)。

## RpcMethodHandler

RpcMethodHandler 是对 RPC Handler 执行的代理，主要是针对数据进行序列化、编码、压缩等。可以参考 [ConcreteRpcService](#concreterpcservice)，在注册 RPC Handler 时，会包装一层 RpcMethodHandler。其最核心的部分就是 Execute 方法：

```cpp
void Execute(const ServerContextPtr& context,
             NoncontiguousBuffer&& req_body,
             NoncontiguousBuffer& rsp_body) override {

    // 传给 RPC Handler 进行处理的是栈上的变量，异步 RPC Handler 最好拷贝后再使用
    RequestType req;
    ResponseType rsp;

    // 解压缩
    auto decompress_type = context->GetCompressType();
    compressor::DecompressIfNeeded(decompress_type, req_body);

    // 反序列化
    uint32_t encode_type = context->GetEncodeType();
    ret = Deserialize(encode_type, &req_body, static_cast<void*>(&req));

    // 设置反序列化后的请求数据
    context->SetRequestData(&req);

    // rpc请求处理前的埋点
    filter_controller_.RunMessageServerFilters(FilterPoint::SERVER_PRE_RPC_INVOKE, context);

    auto status = func_(context, &req, &rsp);

    context->SetResponseData(&rsp);

    // 异步回包
    if (!context->IsResponse()) {
      return;
    }

    // rpc请求处理后的埋点
    filter_controller_.RunMessageServerFilters(FilterPoint::SERVER_POST_RPC_INVOKE, context);

    // 序列化
    Serialize(encode_type, static_cast<void*>(&rsp), rsp_body);

    // 压缩
    compressor::CompressIfNeeded(context->GetRspCompressType(), rsp_body,
                                 context->GetRspCompressLevel());
  }
```

## ServerContext

ServerContext 是个关键的类，提供了请求上下文的相关信息，包括：

- 底层信息结构 basic_info
- 支持同步/异步响应
- 设置响应编码方式
- 设置响应压缩方式

### Async Response

异步响应的第一步是需要设置 `is_response` 为 false：

```cpp
context->SetResponse(false);
```

如此，在 RPC Handler 调用结束的时候并不会立即回包，这在 `UnaryServiceHandler::HandleMessage` 进行的判断：

```cpp
void UnaryServiceHandler::HandleMessage(STransportReqMsg* recv, STransportRspMsg** send) {
  // 创建上下文
  ServerContextPtr context = MakeRefCounted<ServerContext>(*recv);

  // 超时、Filter 等等处理

  // 请求消息分发处理
  service_impl_->Dispatch(context, context->GetRequestMsg(), context->GetResponseMsg());

  // false 则不进行回包
  if (context->IsResponse()) {
    service_impl_->SendUnaryResponse(context, context->GetResponseMsg(), send);
  }
}
```

关于 SendunaryResponse 请参考 [SendunaryResponse](#sendunaryresponse)。

至此，可以使用两种方式来进行异步响应发起：

- SendUnaryResponse(status, rsp)，对于 RPC Service 有效，用于设置响应的 protobuf：

  ```cpp
  // status 为接口调用的结果，biz_rsp 为业务层的数据对象
  template <typename T>
  void SendUnaryResponse(const xrpc::Status& status, const T& biz_rsp) {
    SetResponseData(&biz_rsp);

    // ...

    // protobuf 序列化
    void* rsp = static_cast<void*>(const_cast<T*>(&biz_rsp));
    NoncontiguousBuffer data;
    serialization->Serialize(type, rsp, &data);

    // 数据压缩
    auto compress_type = GetRspCompressType();
    compressor::CompressIfNeeded(compress_type, data, GetRspCompressLevel());

    // 设置响应 body
    rsp_msg_->SetNonContiguousProtocolBody(std::move(data));
    ProcessResponseStatus(true, status);
  }

  void ServerContext::ProcessResponseStatus(bool encode_ret, Status status) {
    GetFilterController().RunMessageServerFilters(FilterPoint::SERVER_POST_RPC_INVOKE, this);

    if (encode_ret) {
      SendUnaryResponse(status);
      return;
    }

    Status encode_status;
    if (adapter_->GetServerCodec() != nullptr) {
      encode_status.SetFrameworkRetCode(
          adapter_->GetServerCodec()->GetProtocolRetCode(xrpc::codec::ServerRetCode::ENCODE_ERROR));
    } else {
      encode_status.SetFrameworkRetCode(XrpcRetCode::XRPC_SERVER_ENCODE_ERR);
    }
    SendUnaryResponse(encode_status);
  }
  ```

- SendUnaryResponse(status), 对于 RPC Service 只会返回一个 status 信息，对于 HTTP Service 这个 status 没有任何意义：

  ```cpp
  void ServerContext::SendUnaryResponse(const xrpc::Status& status) {
    status_ = status;
  
    // filter埋点控制器
    GetFilterController().RunMessageServerFilters(FilterPoint::SERVER_PRE_SEND_MSG, this);

    NoncontiguousBuffer send_data;

    // 编码
    adapter_->GetServerCodec()->ZeroCopyEncode(this, rsp_msg_, send_data);

    auto* send_msg = new STransportRspMsg();
    send_msg->basic_info = GetTransportBasicInfo();
    send_msg->send_data = std::move(send_data);

    SendTransportMsg(send_msg);
  }
  ```

对于 `SendTransportMsg` 会真的进行数据的发送：

```cpp
Status ServerContext::SendTransportMsg(STransportRspMsg* msg) {
  // send msg
  adapter_->SendMsg(msg);

  return kDefaultStatus;
}
```
