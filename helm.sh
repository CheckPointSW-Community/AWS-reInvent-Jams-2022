git clone https://github.com/chkp-ivanmar/cpx-2021-demo.git
echo "Install the attacker client"
helm install -f cpx-2021-demo/attacker-cpx/values.yaml --namespace attacker --create-namespace attacker-client cpx-2021-demo/attacker-cpx

echo "Install our sushi restaurant web page"
helm install -f cpx-2021-demo/cpx-sushi/values.yaml --namespace sushi --create-namespace sushi-restaurant cpx-2021-demo/cpx-sushi
