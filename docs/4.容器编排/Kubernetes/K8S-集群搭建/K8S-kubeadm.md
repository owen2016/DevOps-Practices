﻿# kubeadm 手动搭建kubernetes 集群

[TOC]

**由于k8s部署比较复杂，该文档内容比较多，请耐心阅读，跟着步骤完成操作！**

---

kubeadm是Kubernetes官方提供的用于快速安装Kubernetes集群的工具，通过将集群的各个组件进行容器化安装管理，通过kubeadm的方式安装集群比二进制的方式安装要方便不少。

安装参考- <https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/>

## K8S 组件构成

- kubectl
- kubeadm

- K8s Master
  - kubelet
  - kube-proxy
  - kube-apiserver
  - kube-scheduler
  - kube-controller-manager
  - etcd

- K8s Node
  - kubelet
  - kube-proxy

- calico
- coredns

## 环境准备 (以ubuntu系统为例）

### 1. kubernetes集群机器

| 机器IP | 机器hostname | K8s集群角色 | 机器操作系统 |
| -- | -- | -- | -- |
| 172.20.249.16 | 172-20-249-16 | master | ubuntu16.04 |
| 172.20.249.17 | 172-20-249-17 | node | ubuntu16.04 |
| 172.20.249.18 | 172-20-249-18 | node | ubuntu16.04 |

> 使用如下命令设置hostname: (非必须)

```bash
# 172.20.249.16
hostnamectl --static set-hostname k8s-master
# 172.20.249.17
hostnamectl --static set-hostname k8s-node-01
# 172.20.249.18
hostnamectl --static set-hostname k8s-node-02
```

Kubernetes v1.8+ 要求关闭系统 Swap，请在所有节点利用以下指令关闭 （否则kubelet会出错！）

`swapoff -a && sed -i '/ swap / s/^/#/' /etc/fstab`

### 2. 安装 docker、 kubeadm、kubelet、kubectl

#### 2.1 在每台机器上安装 docker

``` sh
# step 1: 安装必要的一些系统工具
sudo apt-get update
sudo apt-get -y install apt-transport-https ca-certificates curl software-properties-common

# step 2: 安装GPG证书
curl -fsSL http://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo apt-key add -

# Step 3: 写入软件源信息
sudo add-apt-repository "deb [arch=amd64] http://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable"

# Step 4: 更新并安装 Docker-CE (可指定版本)
sudo apt-get -y update
sudo apt-get -y install docker-ce

sudo apt-get -y install docker-ce=17.03.0~ce-0~ubuntu-xenial
```

#### 2.2 每台机器上安装 kubelet 、kubeadm 、kubectl

- kubeadm: the command to bootstrap the cluster.
- kubectl: the command line util to talk to your cluster
- kubelet: the component that runs on all of the machines in your cluster and does things like starting pods and containers.

``` sh
apt-get update && apt-get install -y apt-transport-https

# 安装 GPG 证书
curl https://mirrors.aliyun.com/kubernetes/apt/doc/apt-key.gpg | apt-key add -

# 写入软件源；注意：我们用系统代号为 bionic，但目前阿里云不支持，所以沿用 16.04 的 xenial
cat <<EOF >/etc/apt/sources.list.d/kubernetes.list
deb https://mirrors.aliyun.com/kubernetes/apt/ kubernetes-xenial main
EOF

apt-get update

apt-get install -y kubelet kubeadm kubectl

# 指定版本
apt-get install -y kubelet=1.18.8-00 kubeadm=1.18.8-00 kubectl=1.18.8-00
```

![install-kube](images/install-kubectl.png)

## 创建 kubernetes 集群

### kubeadm

kubeadm是一个构建k8s集群的工具。它提供的`kubeadm init`和 `kubeadm join` 两个命令是快速构建k8s集群的最佳实践。 其次，kubeadm工具只为构建最小可用集群，它只关心集群中最基础的组件，至于其他的插件（比如dashboard、CNI等）则不会涉及

1. kubeadm init to bootstrap the initial Kubernetes control-plane node.

2. kubeadm join to bootstrap a Kubernetes worker node or an additional control plane node, and join it to the cluster.

3. kubeadm upgrade to upgrade a Kubernetes cluster to a newer version.

4. kubeadm reset to revert any changes made to this host by kubeadm init or kubeadm join.

更多了解 kubeadm - <https://www.cnblogs.com/shoufu/p/13047723.html>

### 在 master 节点 init 集群

kubeadm 初始化整个集群的过程，会生成相关的各种证书、kubeconfig 文件、bootstraptoken 等等

**注意：** 如果使用直接使用`kubeadm init`，会使用默认配置（如下）

`kubeadm config print init-defaults --kubeconfig ClusterConfiguration > kubeadm.yml` 可打印默认配置

``` yaml
apiVersion: kubeadm.k8s.io/v1beta2
bootstrapTokens:
- groups:
  - system:bootstrappers:kubeadm:default-node-token
  token: abcdef.0123456789abcdef
  ttl: 24h0m0s
  usages:
  - signing
  - authentication
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 1.2.3.4
  bindPort: 6443
nodeRegistration:
  criSocket: /var/run/dockershim.sock
  name: k8s-master
  taints:
  - effect: NoSchedule
    key: node-role.kubernetes.io/master
---
apiServer:
  timeoutForControlPlane: 4m0s
apiVersion: kubeadm.k8s.io/v1beta2
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controllerManager: {}
dns:
  type: CoreDNS
etcd:
  local:
    dataDir: /var/lib/etcd
imageRepository: k8s.gcr.io
# 默认情况下kubeadm会到k8s.gcr.io拉取镜像，不过对于一些私有化部署（比如国内存在墙的情况下，上面的地址是访问不到的），就需要自定义镜像地址了 如： imageRepository: registry.aliyuncs.com/google_containers
kind: ClusterConfiguration
kubernetesVersion: v1.18.0
networking:
  dnsDomain: cluster.local
  podSubnet: 10.244.0.0/16 # 添加该配置
  serviceSubnet: 10.96.0.0/12
scheduler: {}

```

修改配置文件后， 执行命令 `kubeadm init --config kubeadm.yml`即可

**或者** 直接传递参数执行  （如下）

``` shell
kubeadm init --image-repository registry.aliyuncs.com/google_containers --pod-network-cidr=10.244.0.0/16



#选择flannel作为 Pod 的网络插件，所以需要指定 --pod-network-cidr=10.244.0.0/16
#选择flannel作为 Pod 的网络插件，所以需要指定 --pod-network-cidr=192.168.0.0/16
```

**参数说明：**

```text
--apiserver-advertise-address：这个参数指定了监听的API地址。若没有设置，则使用默认网络接口。

--apiserver-bind-port：这个参数指定了API服务器暴露出的端口号，默认是6443

--kubernetes-version：指定kubeadm安装的kubernetes版本。这个是很重要的，因为默认情况下kubeadm会安装与它版本相同的kubernetes版本

--image-repository 可以指定国内的镜像仓库。 默认k8s.gcr.io 国内无法访问

-- token-ttl：令牌被删除前的时间，默认是24h。kubeadm初始化完毕后会生成一个令牌，让其他节点能够加入集群，过时之后这个令牌会自动删除。如果设置为0之后令牌就永不过期

```

如下所示，`kubeadm init` 会 pull 必要的镜像，可能时间会比较长 (`kubeadm config images pull` 可测试是否可以拉取镜像，如果加了 `--image-repository registry.aliyuncs.com/google_containers`，不会担心在国内拉取镜像问题)

``` text
user@k8s-master:~$ kubeadm config images list
k8s.gcr.io/kube-apiserver:v1.18.9
k8s.gcr.io/kube-controller-manager:v1.18.9
k8s.gcr.io/kube-scheduler:v1.18.9
k8s.gcr.io/kube-proxy:v1.18.9
k8s.gcr.io/pause:3.2
k8s.gcr.io/etcd:3.4.3-0
k8s.gcr.io/coredns:1.6.7

```

init 完后，可以看到如下提示：

![master-init](./images/master-init.png)

按照提示在 master 节点执行以下命令: (**否则会出错**)

``` sh
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

此时， master 处于`ready` 状态

```user@k8s-master:~$ kubectl get nodes
NAME         STATUS   ROLES    AGE   VERSION
k8s-master   Ready    master   14m   v1.18.6
```

### 在worker 节点执行命令 join 到集群

拷贝在 master 节点 init 后的 join 命令，在其他两个 worker 节点执行:

``` sh
kubeadm join 172.20.249.16:6443 --token cma8ob.ow9sfv5erqgkkp30 \
    --discovery-token-ca-cert-hash sha256:def379576eacaddbb4bbf4ca12fbb8a0b77383e4521cbf238f21c8dd3cb80fab
```

可以看到该节点已经加入到集群中去了，然后我们把 master 节点的~/.kube/config文件拷贝到当前节点对应的位置即可使用 kubectl 命令行工具了。

``` sh
mkdir -p $HOME/.kube
# copy master "/etc/kubernetes/admin.conf"
sudo scp root@172.20.249.16:/etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

要注意将上面的加入集群的命令保存下面，如果忘记，可以使用以下命令获取

kubeadm token create --print-join-command

### 安装 Pod Network (在 master 节点 flannel/Calico 网络插件)

在 master 节点查看集群情况,可以看到节点的 status 还是 NotReady，这是由于还没有网络插件。

以 [flannel插件](https://github.com/coreos/flannel/blob/master/Documentation/kubernetes.md) 为例,在 master 节点 执行

``` shell
#For Kubernetes v1.7+
wget https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
kubectl apply -f  kube-flannel.yml
```

Calico插件- 参考 <https://docs.projectcalico.org/getting-started/kubernetes/quickstart>

等待所有的 pod 都是 running 状态，可以看到所有 node 的 status 是 running 的状态，这时 kubernetes 集群就搭建好了。

![node-ready](images/node-ready.png)

至此3个节点的集群搭建完成，后续可以继续添加node节点，或者部署dashboard、helm包管理工具、EFK日志系统、Prometheus Operator监控系统、rook+ceph存储系统等组件

## 部署一个简单示例

`kubectl create -f nginx-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  selector:
    matchLabels:
      app: nginx
  replicas: 3
  strategy:
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:latest
          ports:
            - containerPort: 80
```

发布服务,暴露端口

`kubectl expose deployment nginx-deployment --port=80 --type=LoadBalancer`
