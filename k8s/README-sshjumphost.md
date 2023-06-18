# SSH Jump host

POC for connecting user host (e.g. laptop) with back-end pods (a.k.a ray cluster nodes) without the need to externally expose individual node ports (e.g. NodePort)

Login to user host and perform the following in this order

**Note:** It is assumed you have `kubectl` installed and that it is pointing to the your kubernetes cluster

### create secret

create secret for your public key. It will automatcially added to ssh-jumphost 'autorized_keys'

```
kubectl create secret generic ssh-key-secret-laptop --from-file=ssh-publickey=$HOME/.ssh/id_rsa.pub
```

### deploy ssh-jumphost

automatically starts ssh service exposing port 22 through nodeport

```
kubectl apply -f ./deploy/ubuntu-sshjumphost.yaml
```

### update ssh config

append the below to ~/.ssh/config

```
Host ubuntu-sshserver
  HostName 172.31.3.2
  User root
  IdentityFile /home/weit/.ssh/id_rsa
  IdentitiesOnly yes
  ForwardAgent yes
  StrictHostKeyChecking no
  UserKnownHostsFile=/dev/null
  GlobalKnownHostsFile=/dev/null
  # flannel
  ProxyJump root@10.244.1.99
  # nodeport
  Port 30022
```