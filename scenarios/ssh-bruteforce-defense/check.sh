#!/bin/bash

docker exec cyber_target bash -c "
fail2ban-client status sshd
"