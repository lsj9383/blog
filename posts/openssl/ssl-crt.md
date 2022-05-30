# SSL CRT Config

<!-- TOC -->

- [SSL CRT Config](#ssl-crt-config)
    - [Overview](#overview)
    - [证书及相关文件](#证书及相关文件)
    - [自签证书](#自签证书)
        - [生成服务器自签证书](#生成服务器自签证书)
        - [生成客户端证书](#生成客户端证书)
    - [证书配置](#证书配置)
        - [单向认证](#单向认证)
        - [双向认证](#双向认证)
        - [测试请求](#测试请求)
    - [证书链](#证书链)
        - [服务器证书链](#服务器证书链)
        - [客户端证书链](#客户端证书链)
    - [证书撤销相关的讨论](#证书撤销相关的讨论)
        - [现存标准](#现存标准)
        - [浏览器对于证书撤销的处理](#浏览器对于证书撤销的处理)
        - [Nginx 对于证书撤销的处理](#nginx-对于证书撤销的处理)
        - [通过 openssl 在证书中打入 CRL URL](#通过-openssl-在证书中打入-crl-url)
    - [Nginx 对 CRL 的配置](#nginx-对-crl-的配置)
        - [Root CA 的 CRL 配置](#root-ca-的-crl-配置)
        - [存在中间 CA 的 CRL 配置](#存在中间-ca-的-crl-配置)
    - [附录、参考文献](#附录参考文献)

<!-- /TOC -->

## Overview

SSL 原理这里就直接省略了，仅记录证书相关配置实践。

## 证书及相关文件

初次接触 SSL 会被其繁多的后缀和名词所困惑，只要理解 SSL 原理，这些文件其实是很容理解的：

- `*.key`，这是 SSL 所需要的私钥文件。
- `*.csr`，证书签名请求文件，生成前需要先指定私钥，openssl 会自动生成公钥，并要求生成这填入证书主体信息。本质上就是待签名的证书。
- `*.crt`，这是 SSL 中的证书文件，记录了证书主体、颁发者（CA）、CA 签名算法、CA 私钥的签名等。将 CSR 交给 CA 进行签名得到 CRT文件。
  - CRT 文件支持 Base64 格式和 二进制格式
  - 如果一个文件后缀是 `*.crt` 是无法得知到底是哪种格式。个人感觉 Base64 格式（PEM）较为多见。
- `*.pem`，这是 SSL 证书文件，且明确格式为 Base64。
- `*.der/*.cer`，这是 SSL 证书文件，且明确格式为二进制格式。
- `*.pfx`，同时包含了公钥和私钥的证书文件，通常在双向认证中会涉及。通常有密码保护。

## 自签证书

可以借助 openssl 工具分别生成服务器和客户端的自签证书。

### 生成服务器自签证书

服务器自签证书用于最常见的 SSL 场景，由客户端校验服务器证书，判断是否安全。

```sh
# 生成私有 CA
$ openssl genrsa -out pri_ca.key 2048
$ openssl req -new -x509 -days 3650 -key pri_ca.key -out pri_ca.crt -subj "/C=CN/ST=GuangDong/L=ShenZhen/O=Hello/OU=World/CN=test_ca"

# 生成私钥文件（带密码）
$ openssl genrsa -des3 -out server.key 2048
# 生成 CA 签名请求（本质上就是未带 CA 签名的证书）, 需要确保其中的CN（common name）填写为正确的域名
$ openssl req -new -key server.key -out server.csr
# 也可以快速生成csr
$ openssl req -new -key server.key -out server.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=domain.com"
# 用私有 CA 给 CSR 进行签名, 生成 CRT 证书（PEM格式）
$ openssl x509 -req -days 365 -in server.csr -CA pri_ca.crt -CAkey pri_ca.key -set_serial 01 -out server.crt
# 给私钥文件去出密码（如果没有去除密码，每次加载ngx配置都需要输入密码）
$ mv server.key server.key.bak
$ openssl rsa -in ./server.key.bak -out server.key

# 查看证书信息
$ openssl x509 -noout -text -in server.crt
```

### 生成客户端证书

客户端证书和服务器证书是完全一样的，只是配置的位置不同。客户端证书多用于双向认证的场景。

```sh
# 生成私钥文件（带密码）
$ openssl genrsa -des3 -out client.key 2048
# 生成 CA 签名请求（本质上就是未带 CA 签名的证书）, 需要确保其中的CN（common name）填写为正确的域名
$ openssl req -new -key client.key -out client.csr
# 也可以快速生成csr
$ openssl req -new -key client.key -out client.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=client"
# 用私有 CA 给 CSR 进行签名, 生成 CRT 证书（PEM格式）
$ openssl x509 -req -days 365 -in client.csr -CA pri_ca.crt -CAkey pri_ca.key -set_serial 01 -out client.crt

# 导出可以安装到浏览器的 pfx 证书
$ openssl pkcs12 -export -out client.pfx -inkey client.key -in client.crt -certfile client.crt

# 查看证书信息
$ openssl x509 -noout -text -in client.crt
```

客户端需要 pfx 证书，并在导入浏览器的时候输入密码，用以解开 pfx。

## 证书配置

### 单向认证

```conf
server {
    server_name                     dev-ssl.rail.com.cn;
    listen                          80;
    listen                          443 ssl;

    #------------------------------------------------------------------------------------
    ssl_certificate                 /data/rail/entry/nginx/conf/ssl/test_ca/server.crt;
    ssl_certificate_key             /data/rail/entry/nginx/conf/ssl/test_ca/server.key;
    ssl_session_timeout             5m;
    ssl_protocols                   TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers                     HIGH:!RC4:!MD5:!aNULL:!eNULL:!NULL:!DH:!EDH:!EXP:+MEDIUM;
    ssl_prefer_server_ciphers       on;

    location / {
        return 200 "hello world";
    }
}
```

如果用了自签证书，还需要进行浏览器对私有 CA 证书的受信配置。

需要注意的是，chrome 对证书的认证较为严格，即便是将自签证书的 CA 添加为受信的，也可能会出现 `NET::ERR_CERT_COMMON_NAME_INVALID` 的异常。对于这种情况，需要为 Server 证书添加扩展：

```conf
# ext.conf

authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = {domain}
```

上述 `{domain}` 使用与 Server 证书中的 `CN` 相同的取值即可。通过该扩展生成证书：

```sh
# 扩展信息
$ cat ext.conf
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = domain.com

# 快速生成csr
$ openssl req -new -key server.key -out server.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=domain.com"

# 生成证书
$ openssl x509 -req -days 365 -in server.csr -CA pri_ca.crt -CAkey pri_ca.key -set_serial 01 -out server.crt -extfile domain.com
```

### 双向认证

双向认证主要是打开客户端认证，并指定给客户端签发证书的 `CA 证书`。

```conf
server {
    server_name                     dev-ssl.rail.com.cn;
    listen                          80;
    listen                          443 ssl;

    #------------------------------------------------------------------------------------
    ssl_certificate                 /data/rail/entry/nginx/conf/ssl/test_ca/server.crt;
    ssl_certificate_key             /data/rail/entry/nginx/conf/ssl/test_ca/server.key;
    ssl_session_timeout             5m;
    ssl_protocols                   TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers                     HIGH:!RC4:!MD5:!aNULL:!eNULL:!NULL:!DH:!EDH:!EXP:+MEDIUM;
    ssl_prefer_server_ciphers       on;

    ssl_client_certificate          /data/rail/entry/nginx/conf/ssl/test_ca/test_ca.crt;
    ssl_verify_client on;

    location / {
        return 200 "hello world";
    }
}
```

- ssl_client_certificate, 声明一个受信的 CA 证书，该证书用于校验客户端证书。
- ssl_verify_client, 对客户端进行验证的模式：
  - off, 默认值，不进行校验。
  - on, 对客户端进行校验。
  - optional, 客户端提供了证书就校验，没提供就不校验。
  - optional_no_ca, 要求客户端提供证书，但是不强求客户端证书被受信 CA 签名。

**需要注意：**

- `ssl_client_certificate` 一定是配置给客户端签发的 CA 证书，而不是客户端的证书，因为校验某个证书是否有效，是通过 CA 证书去校验的，这和在浏览器配置给服务器颁发证书的 CA 证书同理。

### 测试请求

```sh
# 单向认证, 需要通过 --cacert 指定受信 CA 证书，该 CA 证书用于校验服务器证书。
curl --resolve 'dev-ssl.rail.com.cn:443:100.109.182.175' "https://dev-ssl.rail.com.cn/test" --cacert ./test_ca.crt

# 双向认证，需要指定客户端私钥和客户端证书（对于浏览器的场景，通过 pfx 文件已经同时将两者告诉给了浏览器）
curl --resolve 'dev-ssl.rail.com.cn:443:100.109.182.175' "https://dev-ssl.rail.com.cn/test" --cacert ./test_ca.crt --key ./client.key --cert ./client.crt:test -v
```

## 证书链

### 服务器证书链

### 客户端证书链

## 证书撤销相关的讨论

### 现存标准

CA 会维护一个撤销证书的列表，等待客户端/服务器查询。

- CRL，证书撤销列表：
  - 客户端：浏览器会去 CA 拉取证书撤销列表，判断证书是否已经被撤销。缺点是 CA 维护的撤销列表往往非常庞大，拉取非常耗时，失败率高。
  - 服务器：服务器会去 CA 拉取证书撤销列表，在服务器上判断证书是否已经被撤销。
- OCSP，在线证书状态协议：
  - 客户端：客户端不会去获取证书列表，而是将待校验证书发给 CA，由 CA 校验。缺点是容易暴露用户的浏览习惯。
  - 服务器：服务器上的 OCSP 又被叫做 OCSP Stapling，由服务器将证书发给 CA 进行校验。

### 浏览器对于证书撤销的处理

由于现存标准的种种缺陷，Chrome/FrieFox 均没有采用 CRL 和 OCSP 的实现，而是采用自己的方式：

- firefox 使用的方案是仅仅记录 CA 中间证书的撤销情况，而不去记录客户端/服务器证书的，这样大大减少了数据量。
- chrome 仅仅会记录权威 CA 的证书撤销情况。

### Nginx 对于证书撤销的处理

Nginx 对于证书撤销的处理较为简单：

- OCSP，Nginx 支持对服务器证书的撤销校验，但是不支持对客户端证书的撤销校验。
- CRL，Nginx 支持从指定的 CRL 文件校验证书，但是不支持从证书的 CRL URL 进行证书校验。

总体而言，Nginx 对证书撤销校验不够彻底。

### 通过 openssl 在证书中打入 CRL URL

Nginx 不支持获取证书中的 CRL URL 进行校验，这里只是做个简单的记录：

```sh
# 将 CRL URL 写入文件
$ vim ext.cnf
crlDistributionPoints=@crl_section

[crl_section]
URI.1 = http://127.0.0.1/crl.pem

# 通过 csr 生成 crt 的时候打入该 CRL URL
$ openssl x509 -req -days 365 -in client.csr -CA pri_ca.crt -CAkey pri_Ca.key -set_serial 01 -out client.crt -extfile ext.cnf

# 查看证书详情
$ openssl x509 -noout -text -in client.crt
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 1 (0x1)
    Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=CN, ST=GuangDong, L=ShenZhen, O=test, OU=test_unit, CN=pri_ca
        Validity
            Not Before: Apr  1 04:03:03 2020 GMT
            Not After : Apr  1 04:03:03 2021 GMT
        Subject: C=cn, ST=asdf, L=cdsa, O=sacd, OU=sadc, CN=sacd/emailAddress=cdas
        Subject Public Key Info:
            Public Key Algorithm: rsaEncryption
                Public-Key: (2048 bit)
                Modulus:
                    ...
                Exponent: 65537 (0x10001)
        X509v3 extensions:
            X509v3 CRL Distribution Points:

                Full Name:
                  URI:http://127.0.0.1/crl.pem

    Signature Algorithm: sha256WithRSAEncryption
         ....
```

## Nginx 对 CRL 的配置

### Root CA 的 CRL 配置

对于最简单的 Root CA 签发的证书撤销（这种情况下没有中间证书）是表简单的。首先需要通过 openssl 进行 CRL 列表生成。

```sh
# 1）先找到 openssl.cnf 文件（每个 node 配置的可能不一样）
$ find / -name openssl.cnf
/etc/pki/tls/openssl.cnf

# 2）将文件拷贝到一个维护 CA 数据库的目录中
$ cd ~/workspace/ca/root_ca
$ cp /etc/pki/tls/openssl.cnf ./openssl.cnf
$ mkdir -p data/private

# 3）在该目录下建立 root_ca，方式在前面章节已经进行了叙述
$ openssl genrsa -out root_ca.key 2048
$ openssl req -new -x509 -days 3650 -key root_ca.key -out root_ca.crt -subj "/C=CN/ST=GuangDong/L=ShenZhen/O=Hello/OU=World/CN=root_ca"

# 4）初始化 data 目录
# 初始化 crl 列表序号
$ echo 1000 > data/crlnumber
# 复制 ca 私钥
$ cp root_ca.key data/private/cakey.pem
# 复制 ca 证书
$ cp root_ca.crt data/cacert.pem
# 该文件实际记录了被撤销的证书
$ touch data/index.txt

# 5）输出 CRL
$ openssl ca -config ./openssl.cnf -gencrl -out root_ca_crl.pem

# 6）查看被撤销的证书列表
$ openssl crl  -noout -text -in root_ca_crl.pem Certificate Revocation List (CRL):
        Version 2 (0x1)
    Signature Algorithm: sha256WithRSAEncryption
        Issuer: /C=CN/ST=GuangDong/L=ShenZhen/O=Hello/OU=World/CN=root_ca
        Last Update: Apr  1 16:28:43 2020 GMT
        Next Update: May  1 16:28:43 2020 GMT
        CRL extensions:
            X509v3 CRL Number:
                4097
No Revoked Certificates.
    Signature Algorithm: sha256WithRSAEncryption
    ...
```

可以看到，当前 CRL 中是没有被撤销的证书的。现在生成三个客户端证书，再用 root_ca 对其进行撤销。

```sh
$ cd ~/workspace/ca/root_ca/client_ca

# 第一个证书 (序号为1)
$ openssl genrsa -des3 -out client1.key 2048
$ openssl req -new -key client1.key -out client1.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=client1"
$ openssl x509 -req -days 365 -in client1.csr -CA ../root_ca.crt -CAkey ../root_ca.key -set_serial 01 -out client1.crt

# 第二个证书 (序号为2)
$ openssl genrsa -des3 -out client2.key 2048
$ openssl req -new -key client2.key -out client2.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=client2"
$ openssl x509 -req -days 365 -in client2.csr -CA ../root_ca.crt -CAkey ../root_ca.key -set_serial 02 -out client2.crt

# 第三个证书 (序号为3)
$ openssl genrsa -des3 -out client3.key 2048
$ openssl req -new -key client3.key -out client3.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=client3"
$ openssl x509 -req -days 365 -in client3.csr -CA ../root_ca.crt -CAkey ../root_ca.key -set_serial 03 -out client3.crt

# 现在撤销前两个证书
$ cd ~/workspace/ca/root_ca
$ openssl ca -config ./openssl.cnf -revoke ./client_ca/client1.crt
$ openssl ca -config ./openssl.cnf -revoke ./client_ca/client2.crt

# 重新生成 CRL 链
$ openssl ca -config ./openssl.cnf -gencrl -out root_ca_crl.pem

# 重新观察撤销证书链，很明显，序号为1和2的证书被撤销了。
$ openssl crl  -noout -text -in root_ca_crl.pem
Certificate Revocation List (CRL):
        Version 2 (0x1)
    Signature Algorithm: sha256WithRSAEncryption
        Issuer: /C=CN/ST=GuangDong/L=ShenZhen/O=Hello/OU=World/CN=root_ca
        Last Update: Apr  1 16:39:09 2020 GMT
        Next Update: May  1 16:39:09 2020 GMT
        CRL extensions:
            X509v3 CRL Number:
                4098
Revoked Certificates:
    Serial Number: 01
        Revocation Date: Apr  1 16:36:35 2020 GMT
    Serial Number: 02
        Revocation Date: Apr  1 16:39:02 2020 GMT
    Signature Algorithm: sha256WithRSAEncryption
         10:27:49:e1:d5:41:33:79:ba:01:b3:79:6c:58
```

在 CRL 生成后，就可以在 Nginx 中制定 CRL 文件。

```conf
server {
    server_name                     ${domain};
    listen                          80;
    listen                          443 ssl;

    #------------------------------------------------------------------------------------
    ssl_certificate                 ${server.crt};
    ssl_certificate_key             ${server.key};
    ssl_session_timeout             5m;
    ssl_protocols                   TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers                     HIGH:!RC4:!MD5:!aNULL:!eNULL:!NULL:!DH:!EDH:!EXP:+MEDIUM;
    ssl_prefer_server_ciphers       on;

    ssl_client_certificate          ${home}/workspace/ca/root_ca/root_ca.crt;
    ssl_verify_client on;

    ssl_crl                         ${home}/workspace/ca/root_ca/root_ca_crl.pem;

    location / {
       return 200 $ssl_client_serial;
    }
}
```

### 存在中间 CA 的 CRL 配置

存在中间 CA 时，相比单个 Root CA 的而言，主要是需要将所有的 CA CRL 进行打包，放到一个文件中，这是为了确保每条证书链的完整性。如果某条证书链的完整性不能得到保证，则校验会失败。root 证书继续沿用之前的配置，现在签发两个中间 CA 证书。

```sh
$ cd ~/workspace/ca/root_ca/

# 目录初始化
$ mkdir -p middle_ca_1/data/private
$ mkdir -p middle_ca_2/data/private

# 生成私钥
$ openssl genrsa -des3 -out middle_ca_1/middle_ca_1.key 2048
$ openssl genrsa -des3 -out middle_ca_2/middle_ca_2.key 2048

# 生成csr
$ openssl req -new -key middle_ca_1/middle_ca_1.key -out middle_ca_1/middle_ca_1.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=middle_ca_1"
$ openssl req -new -key middle_ca_2/middle_ca_2.key -out middle_ca_2/middle_ca_2.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=middle_ca_2"

# 生成证书
$ openssl x509 -req -days 365 -in middle_ca_1/middle_ca_1.csr -CA root_ca.crt -CAkey root_ca.key -set_serial 11 -out middle_ca_1/middle_ca_1.crt
$ openssl x509 -req -days 365 -in middle_ca_2/middle_ca_2.csr -CA root_ca.crt -CAkey root_ca.key -set_serial 22 -out middle_ca_2/middle_ca_2.crt

# 初始化第一个 CA 证书数据库
$ cd ~/workspace/ca/root_ca/middle_ca_1
$ cp /etc/pki/tls/openssl.cnf ./openssl.cnf
$ echo 1001 > data/crlnumber
$ cp middle_ca_1.key data/private/cakey.pem
$ cp middle_ca_1.crt data/cacert.pem
$ touch data/index.txt

# 初始化第二个 CA 证书数据库
$ cd ~/workspace/ca/root_ca/middle_ca_2
$ cp /etc/pki/tls/openssl.cnf ./openssl.cnf
$ echo 1002 > data/crlnumber
$ cp middle_ca_2.key data/private/cakey.pem
$ cp middle_ca_2.crt data/cacert.pem
$ touch data/index.txt

# 把所有的 CA 证书进行打包:
$ cd ~/workspace/ca/root_ca/
$ cp root_ca.crt bundle_ca.crt
$ cat middle_ca_1/middle_ca_1.crt >> bundle_ca.crt
$ cat middle_ca_2/middle_ca_2.crt >> bundle_ca.crt

# ！！！注意：修改 openssl 中的 default_ca 的目录
```

现在有了三个 CA：一个 Root CA，两个中间 CA。接下来，可以给每个 CA 生成 CRL 文件，再进行整合为 `bundle_crl.pem` ：

```sh
# Root CA 的 root_ca_crl.pem 已经生成过了，不用再生成了
$ cd ~/workspace/ca/root_ca/middle_ca_1
$ openssl ca -config ./openssl.cnf -gencrl -out middle_ca_1_crl.pem

$ cd ~/workspace/ca/root_ca/middle_ca_2
$ openssl ca -config ./openssl.cnf -gencrl -out middle_ca_2_crl.pem

# 整合 CRL
$ cd ~/workspace/ca/root_ca
$ cp root_ca_crl.pem bundle_crl.pem
$ cat middle_ca_1/middle_ca_1_crl.pem >> bundle_crl.pem
$ cat middle_ca_2/middle_ca_2_crl.pem >> bundle_crl.pem
```

`bundle_crl.pem` 就是一个具有完整 CA 链的 CRL，被 Nginx 的 `ssl_crl` 参数配置。在此之前，先让我们用中间证书生成客户端证书，每个中间 CA 生成两个客户端证书：

```sh
# 创建第一个中间 CA 的客户端证书
$ cd ~/workspace/ca/root_ca/middle_ca_1
$ mkdir client_ca
$ cd client_ca

# 第一个
$ openssl genrsa -des3 -out client11.key 2048
$ openssl req -new -key client11.key -out client11.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=client11"
$ openssl x509 -req -days 365 -in client11.csr -CA ../middle_ca_1.crt -CAkey ../middle_ca_1.key -set_serial 111 -out client11.crt

# 第二个
$ openssl genrsa -des3 -out client12.key 2048
$ openssl req -new -key client12.key -out client12.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=client12"
$ openssl x509 -req -days 365 -in client12.csr -CA ../middle_ca_1.crt -CAkey ../middle_ca_1.key -set_serial 112 -out client12.crt

# 创建第二个中间 CA 的客户端证书
$ cd ~/workspace/ca/root_ca/middle_ca_2
$ mkdir client_ca
$ cd client_ca

# 第一个
$ openssl genrsa -des3 -out client21.key 2048
$ openssl req -new -key client21.key -out client21.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=client21"
$ openssl x509 -req -days 365 -in client21.csr -CA ../middle_ca_2.crt -CAkey ../middle_ca_2.key -set_serial 221 -out client21.crt

# 第二个
$ openssl genrsa -des3 -out client22.key 2048
$ openssl req -new -key client22.key -out client22.csr -subj "/C=CN/ST=gd/L=sz/O=t/OU=wg/CN=client22"
$ openssl x509 -req -days 365 -in client22.csr -CA ../middle_ca_2.crt -CAkey ../middle_ca_2.key -set_serial 222 -out client22.crt
```

现在将第一个中间 CA 证书进行撤销，然后再将第二个中间 CA 的第一个客户端证书撤销：

```sh
$ cd ~/workspace/ca/root_ca
$ openssl ca -config ./openssl.cnf -revoke ./middle_ca_1/middle_ca_1.crt
$ openssl ca -config ./openssl.cnf -gencrl -out root_ca_crl.pem

$ cd ~/workspace/ca/root_ca/middle_ca_2
$ openssl ca -config ./openssl.cnf -revoke ./client_ca/client21.crt
$ openssl ca -config ./openssl.cnf -gencrl -out middle_ca_2_crl.pem

# 重新整合 CRL
$ cd ~/workspace/ca/root_ca
$ cp root_ca_crl.pem bundle_crl.pem
$ cat middle_ca_1/middle_ca_1_crl.pem >> bundle_crl.pem
$ cat middle_ca_2/middle_ca_2_crl.pem >> bundle_crl.pem
```

最后再来看 Nginx 的配置:

```conf
server {
    server_name                     dev-ssl.rail.com.cn;
    listen                          80;
    listen                          443 ssl;
    error_log   logs/error_test_ra.log  debug;

    #------------------------------------------------------------------------------------
    ssl_certificate                 ${server.crt};
    ssl_certificate_key             ${server.key};
    ssl_session_timeout             5m;
    ssl_protocols                   TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers                     HIGH:!RC4:!MD5:!aNULL:!eNULL:!NULL:!DH:!EDH:!EXP:+MEDIUM;
    ssl_prefer_server_ciphers       on;

    ssl_client_certificate          ${home}/workspace/ca/root_ca/bundle_ca.crt;
    ssl_verify_client on;
    # !!! 一定要配置 CA 链深度
    ssl_verify_depth 2;

    ssl_crl                         ${home}/workspace/ca/root_ca/bundle_crl.pem;

    location / {
        return 200 $ssl_client_serial;
    }
}
```

## 附录、参考文献

- [ngx_http_ssl_module](http://nginx.org/en/docs/http/ngx_http_ssl_module.html)
- [SSL 证书格式普及](https://blog.freessl.cn/ssl-cert-format-introduce/)
- [证书各个字段的含义](https://www.cnblogs.com/iiiiher/p/8085698.html)
- [细说 CA 和证书](https://www.barretlee.com/blog/2016/04/24/detail-about-ca-and-certs/)
- [SSL certificate revocation and how it is broken in practice](https://medium.com/@alexeysamoshkin/how-ssl-certificate-revocation-is-broken-in-practice-af3b63b9cb3)
- [CRL RFC 5280](https://tools.ietf.org/html/rfc5280)
