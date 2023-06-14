# SkyPilot k8s

Instructions to run your skypilot tasks against kubernetes cluster.

**Note:** This page is work in progress and not finalized yet.

Login to the host (laptop) where you intend to invoke your skypilot tasks

## Prerequisites

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

update `<REGISTRY>` correct registry

```
export REGISTRY=172.31.3.2
export IMAGE=$REGISTRY/laptop_docker
```

build the image

```
cd ~
docker build --tag "$IMAGE" -f skypilot/Dockerfile_laptop .
```

push the image

```
docker push "$IMAGE"
```

## Deploy 'laptop' into k8s

### Deploy pod and roles

update `<registry ip>` inside yaml file with correct registry

```
kubectl apply -f ./deploy-laptop.yaml
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

## Dev (build base image)

```
export REGISTRY=172.31.3.2
export IMAGE=$REGISTRY/laptop_docker-base
```

```
docker build --tag $IMAGE -f skypilot/Dockerfile_laptop.base .
```
