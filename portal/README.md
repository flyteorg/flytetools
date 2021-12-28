# What's Portal

Portal is a container containing a set of tools to help debug live services.. It can be deployed as a pod or a deployment to give you access to databases and 
other IAM- or VPC- protected services.

## Apply portal deployment

Create portal deployment in `flyte` namespace:

```bash
kubectl apply -f https://raw.githubusercontent.com/flyteorg/flytetools/master/portal/deployment.yaml
```

### Use a different namespace

```bash
curl https://raw.githubusercontent.com/flyteorg/flytetools/master/portal/deployment.yaml | sed "s/namespace: flyte/namespace: union/" | kubectl apply -f -
```

### Use a different service account

```bash
curl https://raw.githubusercontent.com/flyteorg/flytetools/master/portal/deployment.yaml | sed "s/serviceAccountName: default/serviceAccountName: foo/" | kubectl apply -f -
```

## Open a shell into the deployed pod

```bash
kubectl exec -it -n flyte deploy/portal -- bash
```

## Tools available inside:

- [X] postgresql-client (run `psql`)
- [X] redis-client (run `redis-cli`)
- [X] flytekit
- [X] python3
