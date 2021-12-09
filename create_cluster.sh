#create a K8s cluster
export EKS_CLUSTER=CheckPointJamsEKS
echo "export EKS_CLUSTER=CheckPointJamsEKS"  | tee -a ~/.bash_profile

export ZONES="${AWS_REGION}a,${AWS_REGION}b,${AWS_REGION}c"
echo "export ZONES=${ZONES}" | tee -a ~/.bash_profile

eksctl create cluster --name ${EKS_CLUSTER} --version 1.21 --region ${AWS_REGION} --node-type t2.xlarge --nodes 2 --zones ${ZONES}

aws eks update-kubeconfig --name ${EKS_CLUSTER} --region ${AWS_REGION}
