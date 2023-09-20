#!/bin/bash


docker build -t europe-southwest1-docker.pkg.dev/mm-maneds-sta/campaign-server-repo/campaign-server:1.1 .

docker tag europe-southwest1-docker.pkg.dev/mm-maneds-sta/campaign-server:1.1 europe-southwest1-docker.pkg.dev/mm-maneds-sta/campaign-server-repo/campaign-server:1.1
docker push europe-southwest1-docker.pkg.dev/mm-maneds-sta/campaign-server-repo/campaign-server:1.1
kubectl run campaign-server --image=europe-southwest1-docker.pkg.dev/mm-maneds-sta/campaign-server-repo/campaign-server:1.0

