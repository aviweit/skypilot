# SSH Jump host

POC for connecting user host (e.g. laptop) with back-end pods (a.k.a ray cluster nodes) without the need to externally expose individual node ports (e.g. NodePort)

Login to user host and perform the following in this order

**Note:** It is assumed you have `kubectl` installed and that it is pointing to the your kubernetes cluster

### create secret

create secret for your public key. It will be automatically added to ssh-jumphost's and server's 'authorized_keys'

```
kubectl create secret generic ssh-key-secret-laptop --from-file=ssh-publickey=$HOME/.ssh/id_rsa.pub
```

### deploy ssh-server

```
kubectl apply -f ./deploy/ubuntu-sshserver.yaml
```

### deploy ssh-jumphost

automatically starts ssh service exposing port 22 through nodeport (30022)

```
kubectl apply -f ./deploy/ubuntu-sshjumphost.yaml
```

### update ssh config

append the below to ~/.ssh/config

```
Host ubuntu-sshserver
  # internal pod ipaddress
  # or service name of this pod
  HostName 10.244.2.125
  User weit
  IdentityFile /home/weit/.ssh/id_rsa
  IdentitiesOnly yes
  ForwardAgent yes
  StrictHostKeyChecking no
  UserKnownHostsFile=/dev/null
  GlobalKnownHostsFile=/dev/null
  # nodeport
  ProxyJump 172.31.3.2:30022
```

### SSH into ssh server via jump host

you can either provide explicit pod ip or its service name

`ssh  -i ~/.ssh/id_rsa -J 172.31.3.2:30022 10.244.2.125` or `ssh  -i ~/.ssh/id_rsa  -J 172.31.3.2:30022 sshserver`

another option would be to ssh into <Host> which is defined under ~/.ssh/config

`ssh ubuntu-sshserver`
