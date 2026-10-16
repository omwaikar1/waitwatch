#!/usr/bin/env bash
# Delete EVERYTHING WaitWatch created on AWS, so it stops costing money.
#   deploy/aws-teardown.sh
# Irreversible: the server's disk (including the production database) is deleted.
set -euo pipefail
NAME=waitwatch

read -r -p "Delete the WaitWatch server, its disk, IP, firewall and key pair? Type 'delete': " ok
[ "$ok" = "delete" ] || { echo "Cancelled."; exit 1; }

ID=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=$NAME" \
  "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].InstanceId' --output text)

ALLOC=$(aws ec2 describe-addresses --filters "Name=tag:Name,Values=$NAME" \
  --query 'Addresses[].AllocationId' --output text)
for a in $ALLOC; do
  ASSOC=$(aws ec2 describe-addresses --allocation-ids "$a" --query 'Addresses[0].AssociationId' --output text)
  [ "$ASSOC" != "None" ] && aws ec2 disassociate-address --association-id "$ASSOC"
  aws ec2 release-address --allocation-id "$a" && echo "released Elastic IP $a"
done

if [ -n "$ID" ]; then
  aws ec2 terminate-instances --instance-ids $ID > /dev/null && echo "terminating $ID…"
  aws ec2 wait instance-terminated --instance-ids $ID && echo "terminated (disk deleted with it)"
fi

SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$NAME-sg" \
  --query 'SecurityGroups[].GroupId' --output text)
if [ -n "$SG" ]; then
  # AWS can take a minute to release the terminated server's network card, so retry
  for i in $(seq 1 12); do
    aws ec2 delete-security-group --group-id "$SG" 2>/dev/null && { echo "deleted security group $SG"; break; }
    [ "$i" = 12 ] && { echo "could not delete $SG yet; re-run this script in a few minutes"; exit 1; }
    sleep 10
  done
fi

aws ec2 delete-key-pair --key-name "$NAME" && echo "deleted key pair $NAME"
echo "Done. Nothing named '$NAME' is left running."
