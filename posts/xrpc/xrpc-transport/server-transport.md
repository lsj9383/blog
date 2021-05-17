# Xrpc Server Transport

<!-- TOC -->

- [Xrpc Server Transport](#xrpc-server-transport)
    - [Overview](#overview)
    - [Quick Start](#quick-start)
    - [UML Class Diagram](#uml-class-diagram)
    - [Sequence Diagram](#sequence-diagram)
    - [Server Transport](#server-transport)
        - [ServerTransport Initial](#servertransport-initial)
    - [BindAdapter](#bindadapter)
    - [ConnectionManager](#connectionmanager)
    - [Options](#options)

<!-- /TOC -->

## Overview

## Quick Start

## UML Class Diagram

```mermaid
classDiagram

ServerTransport <|-- ServerTransportImpl
ServerTransportImpl --> BindAdapter
BindAdapter --> ConnectionManager

class ServerTransport {
  +Name()
  +Type()
  +Bind()
  +Listen()
  +SendMsg(STransportReqMsg) Future_STransportRspMsg
  +AcceptConnection(AcceptConnectionInfo) bool
  +GetAdapters() vector<BindAdapter*>
}

class ServerTransportImpl {
  +ServerTransportImplOptions options_
  vector<BindAdapter*> bind_adapters_
  +Name()
  +Type()
  +Bind()
  +Listen()
  +SendMsg(STransportReqMsg) Future_STransportRspMsg
  +AcceptConnection(AcceptConnectionInfo) bool
  +GetAdapters() vector<BindAdapter*>
}

class BindAdapter {
  +BindAdapterOptions options_
  +ConnectionManager conn_manager_
  +map<uint64_t, uint64_t> connections_active_time_
  +connection_idle_timeout_
  +AcceptorPtr acceptor_
  +Listen()
  +Bind(bind_type)
  +SendMsg(STransportRspMsg) int
  +CleanConnection(conn)
}

class ConnectionManager {
  +uint32_t reactor_id_
  +uint32_t max_slot_num_
  +uint32_t max_conn_num_
  +queue<uint64_t> free_
  +vector<Connection*> list_
  +uint32_t cur_conn_num_
  +Init(max_conn_num)
  +GenConnectionId() uint64_t
  +AddConnection(conn) bool
  +GetConnection(connection_id) Connection
  +DelConnection(connection_id)
}
```

## Sequence Diagram

## Server Transport

### ServerTransport Initial

## BindAdapter

## ConnectionManager

## Options
