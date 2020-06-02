#!/bin/bash
SERVER='localhost:8001'
while true;
    do
        for PODNAME in $(kubectl --server $SERVER get pods -o json | jq '.items[] | select(.spec.schedulerName == "my-scheduler") | select(.spec.nodeName == null) | .metadata.name' | tr -d '"');
        do
            NODES=($(kubectl --server $SERVER get nodes -o json | jq '.items[].metadata.name' | tr -d '"'))
            NUMNODES=${#NODES[@]}
            CHOSEN=${NODES[$[ $RANDOM % $NUMNODES ]]}
            curl --header "Content-Type:application/json" --request POST --data '{"apiVersion":"v1","kind":"Binding","metadata":{"name":"'$PODNAME'"},"target":{"apiVersion":"v1","kind":"Node","name":"'$CHOSEN'"}}' http://$SERVER/api/v1/namespaces/default/pods/$PODNAME/binding/
            echo "Assigned $PODNAME to $CHOSEN"
        done
        sleep 1
    done
#需要运行环境中先安装jq工具（sudo apt install jq -y）
#需要先运行kubectl proxy为该脚本提供支持
#该脚本实现随机选择一个Node进行调度的策略