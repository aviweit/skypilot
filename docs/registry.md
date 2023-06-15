# Private registry

Allocate a dedicated VM Ubuntu 20.04 with: 2 vCPU, 8 GB RAM, 100 GB disk (or more depending on the images to store)

**Important:** ensure this VM is accessible from all worker nodes

## Start private docker registry

Log into the VM where the registry is going to run

```
sudo docker run -d -p 5000:5000 --name registry registry:2
```

Note: It's **important** to use port `5000`

## Update docker client nodes

become sudo (`sudo -s`)

Do this for all master and worker nodes

```
mkdir -p /etc/docker
vi /etc/docker/daemon.json
```

add the registry with VM's public ipaddress e.g.

```
{
  "insecure-registries":["172.31.3.2:5000"]
}
```

restart docker

```
service docker stop
service docker start
```

exit sudo