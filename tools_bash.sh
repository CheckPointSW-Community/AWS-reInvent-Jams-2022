"#!/bin/bash"

sudo amazon-linux-extras enable docker

sudo yum clean metadata

cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOF

# Install jq command-line tool for parsing JSON, and bash-completion
sudo yum -y install jq gettext bash-completion moreutils docker git go kubectl

# Install Helm
wget https://get.helm.sh/helm-v3.6.0-linux-amd64.tar.gz
tar -zxvf helm-v3.6.0-linux-amd64.tar.gz
sudo cp linux-amd64/helm /usr/local/bin/helm

#install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Set the ACCOUNT_ID and the region to work with our desired region
export AWS_REGION=$(curl -s 169.254.169.254/latest/dynamic/instance-identity/document | jq -r '.region')
test -n "$AWS_REGION" && echo AWS_REGION is "$AWS_REGION" || echo AWS_REGION is not set

# Configure .bash_profile
mkdir /home/ssm-user
export ACCOUNT_ID=$(sudo aws sts get-caller-identity --output text --query Account)
echo "export ACCOUNT_ID=${ACCOUNT_ID}" | tee -a ~/.bash_profile
echo "export ACCOUNT_ID=${ACCOUNT_ID}" | tee -a /home/ec2-user/.bash_profile
#echo "export ACCOUNT_ID=${ACCOUNT_ID}" | tee -a /home/ssm-user/.bash_profile

echo "export AWS_REGION=${AWS_REGION}" | tee -a ~/.bash_profile
echo "export AWS_REGION=${AWS_REGION}" | tee -a /home/ec2-user/.bash_profile

aws configure set default.region ${AWS_REGION}
aws configure get default.region

#enable kubectl bash_completion
echo "source <(kubectl completion bash)" >> ~/.bashrc
echo "source <(kubectl completion bash)" >> /home/ec2-user/.bashrc

#create a K8s cluster
export EKS_CLUSTER=CheckPointJamsEKS
echo "export EKS_CLUSTER=CheckPointJamsEKS"  | tee -a ~/.bash_profile
echo "export EKS_CLUSTER=CheckPointJamsEKS"  | tee -a /home/ec2-user/.bash_profile


export ZONES="${AWS_REGION}a,${AWS_REGION}b,${AWS_REGION}c"
echo "export ZONES=${ZONES}" | tee -a ~/.bash_profile

eksctl create cluster --name ${EKS_CLUSTER} --version 1.21 --region ${AWS_REGION} --nodes 2 --managed=false --zones ${ZONES} --asg-access --external-dns-access --full-ecr-access --appmesh-access --alb-ingress-access --instance-selector-vcpus=4 --instance-selector-memory=16 --instance-selector-gpus=0 --managed=true --max-pods-per-node=25

aws eks update-kubeconfig --name ${EKS_CLUSTER} --region ${AWS_REGION}

# copy .kube to ec2-user and ssm-user
cp .kube/ /home/ec2-user/. -R
mkdir /home/ssm-user
cp .kube/ /home/ssm-user/. -R
chown ec2-user /home/ec2-user/.kube/ -R