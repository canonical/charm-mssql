# Deployment Preparation

This charm deploys on top of Kubernetes. It uses a submodule called the 
operator framework. If you are deploying from the charm store, this step is not
necessary. If you are cloning from source, you need to update the
submodule:
```
git clone https://github.com/canonical/charm-mssql.git
git submodule init
git submodule update
```
For developers of this charm, to fetch the latest updates in the operator
framework, you need to pull the submodule git repository:
```
git submodule foreach git pull origin master
```

# MicroK8s Setup

```
sudo snap install juju --classic --channel 2.8/candidate #or higher, stable version. 2.8 minimum
sudo snap install microk8s --classic
microk8s.enable dns dashboard registry storage
juju bootstrap microk8s
juju add-model mssql
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

#TODO: Set up as secret instead of env var once this is pushed LP:1858515
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

If you are deploying locally on top of MicroK8s, the service is reachable over
the port-forwarding configuration. For example, for a service exposed like this:
```
NAMESPACE NAME           TYPE          CLUSTER-IP     EXTERNAL-IP  PORT(S)
mssql     service/mssql  LoadBalancer  10.152.183.16  <pending>    1443:32542/TCP
```
And a host of IP `192.168.1.75`, then the service would be reachable at
`192.168.1.75:32542`. 

# SQL Utility
To communicate with the database, the sql utility comes handy. Instructions to
install it on ubuntu are available here 
https://docs.microsoft.com/en-us/sql/linux/sql-server-linux-setup-tools?view=sql-server-ver15#ubuntu .

An example of command to connect to the database would be:
`sqlcmd -S 192.168.1.75,32038  -U sa -P "MyC0m9l&xP@ssw0rd"`
