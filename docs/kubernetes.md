# Bootstrap Kubernetes Cluster v1.26.1

Follow these instructions to install Kubernetes cluster.

Create Ubuntu 20.04 VMs with 2vCPUs 8GB RAM 100 GB disk

**For all VMs (master and nodes) perform the below:**

## Docker CE 23.0.0
Update packages

```
sudo apt-get update
sudo apt-get upgrade
```
The below commands are taken from the [docker installation guide](https://docs.docker.com/engine/install/ubuntu/).

```
sudo apt-get update
```

Install some utilities

```
sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
```

Add the key and ensure its fingerprint

```
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

Register docker repository

```
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

Install docker 23.0.0

```
VERSION_STRING=5:23.0.0-1~ubuntu.20.04~focal
sudo apt-get install docker-ce=$VERSION_STRING docker-ce-cli=$VERSION_STRING containerd.io docker-buildx-plugin docker-compose-plugin
```

Verify docker

```
sudo docker run hello-world
```

## Docker tips

### Clean system with unused image, containers, networks

https://docs.docker.com/config/pruning/

```
sudo docker system prune
```

## Turn swap off

```
sudo swapoff -a
```

Run `sudo vi /etc/fstab` and comment out swap partition

Invoke `top` and ensure swap not used


## Kubelet, Kubectl, Kubeadm

The below commands are taken from [install-kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)

run the below to install the exact versions of kubernetes plane on your node

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl
sudo curl -fsSLo /etc/apt/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -qy kubelet=1.26.1-00 kubectl=1.26.1-00 kubeadm=1.26.1-00 kubernetes-cni=1.2.0-00
sudo apt-mark hold kubelet kubeadm kubectl
```

## Golang

Golang is needed for building `cri-dockerd`

The below commands are taken from [install-go](https://go.dev/doc/install)

```bash
cd ~
wget https://go.dev/dl/go1.20.linux-amd64.tar.gz
```

run under sudo

```bash
rm -rf /usr/local/go && tar -C /usr/local -xzf go1.20.linux-amd64.tar.gz
```

exit sudo

Add `export PATH=$PATH:/usr/local/go/bin` to `~/.profile` then

```
source ~/.profile
```

## cri-dockerd

Install `cri-dockerd` following the instructions [in that source code repository](https://github.com/Mirantis/cri-dockerd/tree/v0.3.1).

```bash
cd ~
git clone -b v0.3.1 https://github.com/Mirantis/cri-dockerd
cd cri-dockerd
```

```bash
mkdir bin
go build -v -o bin/cri-dockerd
```

run these under sudo

```bash
mkdir -p /usr/local/bin
install -o root -g root -m 0755 bin/cri-dockerd /usr/local/bin/cri-dockerd
cp -a packaging/systemd/* /etc/systemd/system
sed -i -e 's,/usr/bin/cri-dockerd,/usr/local/bin/cri-dockerd,' /etc/systemd/system/cri-docker.service
systemctl daemon-reload
systemctl enable cri-docker.service
systemctl enable --now cri-docker.socket
```

## kubeadm init (master node)

**Log into master node**

run the below under sudo

**Note:** provide `--apiserver-advertise-address` in case a different ipaddress is being used than the default one

```
kubeadm init --apiserver-advertise-address=<alternate IP> --pod-network-cidr=10.244.0.0/16 --cri-socket=unix:///var/run/cri-dockerd.sock
```

Exit `sudo`

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

Install flannel as default CNI. The below taken from [here](https://github.com/coreos/flannel/blob/master/README.md#deploying-flannel-manually)

```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/download/v0.21.0/kube-flannel.yml
```

Wait until all running

```
kubectl get pod --all-namespaces
```

## kubeadm join (worker nodes)

**Log into a worker node and become root (sudo -s)**

Invoke the `kubeadm join ... --cri-socket=unix:///var/run/cri-dockerd.sock` command that kube init printed in master node **appending cri-socket parameter**

On kubernetes master, list the nodes and ensure your VM appears

```
kubectl get nodes -o wide
```

## Private registry

If needed, setup private registry per [these](./registry.md) instructions
