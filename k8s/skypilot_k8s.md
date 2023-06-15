# SkyPilot k8s

Instructions to run your skypilot tasks against kubernetes cluster.

**Note: This page is work in progress and not finalized yet**

Login to the host (laptop) where you intend to invoke your skypilot tasks

## Prerequisites

### Kubernetes cluster

Use [these instructions](docs/kubernetes.md) to deploy kubernetes cluster with master/workers installed with a VM of Ubuntu 20.04 allocated with 2vCPUs, 8GB RAM and 100 GB disk

### Registry VM

Create fresh Ubuntu 20.04 VM with: 2 vCPU, 8 GB RAM, 100 GB disk

Install docker registry using [these](./docs/registry.md) instructions

### User host (laptop)

The following assumptions should be met

* `kubectl` installed. Refer to https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
* it is assumed that your k8s credentials appear under `~/.kube/config`
* it is assumed that your host is installed with docker

## Prepare the laptop image

### Clone this repository

```
cd ~
git clone https://github.com/aviweit/skypilot.git
cd skypilot
git checkout k8s_cloud-laptop_container
```

### Build laptop docker image

update `<REGISTRY>` with correct registry info

```
export REGISTRY=172.31.3.2:5000
export IMAGE=$REGISTRY/laptop
```

build the image

```
make laptop
```

push the image

```
docker tag sky/laptop "$IMAGE"
docker push "$IMAGE"
```

## Deploy 'laptop' into k8s

### Deploy pod and roles

```
envsubst < deploy/laptop.yaml.template | kubectl apply -f -
```

### [TEMP] ensure ssh secrets are deleted before every 'laptop' deployment

```
kubectl delete secret ssh-key-secret
```

## Invoke skypilot task

Login to 'laptop' pod

```
kubectl exec -it laptop-pod bash
```

```
sky launch hello.yaml
```
