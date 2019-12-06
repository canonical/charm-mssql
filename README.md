# Deployment Preparation

In order to use the charm, you need to place the Operator Framework modules 
under lib. Use `Makefile` to do that:

```
make build
```

# MicroK8s Setup

```
sudo snap install juju --classic
sudo snap install microk8s --classic
microk8s.enable dns dashboard registry storage
juju bootstrap microk8s
juju create-storage-pool operator-storage kubernetes storage-class=microk8s-hostpath
juju deploy ./mssql
```

# MSSQL config options
`MSSQL_PID value`: "Developer": Sets the container to run SQL Server Developer 
edition. Developer edition is not licensed for production data. If the 
deployment is for production use, set the appropriate edition (Enterprise, 
Standard, or Express).
For more information, see How to license SQL Server: 
https://www.microsoft.com/sql-server/sql-server-2017-pricing.

`persistentVolumeClaim`: This value requires an entry for claimName: that maps 
to the name used for the persistent volume claim. This tutorial uses mssql-data.

`SA_PASSWORD`: Configures the container image to set the SA password, 
as defined in this section.
```
valueFrom:
  secretKeyRef:
    name: mssql
    key: SA_PASSWORD
```
When Kubernetes deploys the container, it refers to the secret named `mssql`
to get the value for the password.

By using the `LoadBalancer` service type, the SQL Server instance is accessible 
remotely (via the internet) at port 1433.