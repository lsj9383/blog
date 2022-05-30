# CentOS 下构建 Chromium

<!-- TOC -->

- [CentOS 下构建 Chromium](#centos-下构建-chromium)
    - [Linux 安装依赖](#linux-安装依赖)
    - [安装 Chromium](#安装-chromium)
    - [运行 Demo](#运行-demo)

<!-- /TOC -->

CentOS 构建 Chromium，主要参考了 [Checking out and building Chromium on Linux](https://chromium.googlesource.com/chromium/src/+/master/docs/linux/build_instructions.md)。

## Linux 安装依赖

- Python 2.7 or Python 3.x
- 安装 ninga:

  ```sh
  <https://github.com/ninja-build/ninja/wiki/Pre-built-Ninja-packages>

  yum install install ninja-build
  ```

- 安装 gn:

  ```sh
  <https://gn.googlesource.com/gn/>

  git clone https://gn.googlesource.com/gn
  cd gn
  python build/gen.py
  ninja -C out
  ```

- GLIBC_2.18

  ```sh
  <https://blog.csdn.net/qq_39295044/article/details/86685789>

  wget http://mirrors.ustc.edu.cn/gnu/libc/glibc-2.18.tar.gz
  tar -zxvf glibc-2.18.tar.gz
  mkdir build
  cd build/
  ../configure --prefix=/usr --disable-profile --enable-add-ons --with-headers=/usr/include --with-binutils=/usr/bin
  make -j 8
  make install
  strings /lib64/libc.so.6 | grep GLIBC
  ```

## 安装 Chromium

```sh
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git

# 添加到 PATH 以便使用其中的工具
export PATH="$PATH:/path/to/depot_tools"

mkdir chromium && cd chromium

# fetch 是 depot_tools 中的工具
fetch --nohooks --no-history chromium

# 安装第三方依赖
su -c 'yum install git python bzip2 tar pkgconfig atk-devel alsa-lib-devel \
bison binutils brlapi-devel bluez-libs-devel bzip2-devel cairo-devel \
cups-devel dbus-devel dbus-glib-devel expat-devel fontconfig-devel \
freetype-devel gcc-c++ glib2-devel glibc.i686 gperf glib2-devel \
gtk3-devel java-1.*.0-openjdk-devel libatomic libcap-devel libffi-devel \
libgcc.i686 libgnome-keyring-devel libjpeg-devel libstdc++.i686 libX11-devel \
libXScrnSaver-devel libXtst-devel libxkbcommon-x11-devel ncurses-compat-libs \
nspr-devel nss-devel pam-devel pango-devel pciutils-devel \
pulseaudio-libs-devel zlib.i686 httpd mod_ssl php php-cli python-psutil wdiff \
xorg-x11-server-Xvfb'

gclient runhooks

# 生成目录
gn gen out/Default

autoninja -C out/Default quic_server quic_client
```

## 运行 Demo

```sh
<https://www.chromium.org/quic/playing-with-quic>

# 初始化服务器数据
mkdir /tmp/quic-data
cd /tmp/quic-data
wget -p --save-headers https://www.example.org

# 生成证书
cd net/tools/quic/certs
./generate-certs.sh
cd -

# 启动 Server
./out/Default/quic_server \
  --quic_response_cache_dir=/tmp/quic-data/www.example.org \
  --certificate_file=net/tools/quic/certs/out/leaf_cert.pem \
  --key_file=net/tools/quic/certs/out/leaf_cert.pkcs8

# 启动 Client
./out/Default/quic_client --host=127.0.0.1 --port=6121 https://www.example.org/ --disable_certificate_verification
# ./out/Default/quic_client --host=127.0.0.1 --port=6121 https://www.example.org/ --allow_unknown_root_cert
# 可以通过 --v=1 增加日志
```
