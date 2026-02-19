#!/usr/bin/env bash

#==============================================
# OpenShift or non-sudo environments support
# https://docs.openshift.com/container-platform/3.11/creating_images/guidelines.html#openshift-specific-guidelines
#==============================================

# chown Home dir
sudo chown -R ${USER_NAME}:${USER_NAME} ${HOME}
sudo chmod -R 777 ${HOME}

if ! whoami &> /dev/null; then
  if [ -w /etc/passwd ]; then
    echo "${USER_NAME:-default}:x:$(id -u):0:${USER_NAME:-default} user:${HOME}:/sbin/nologin" >> /etc/passwd
  fi
fi

# Load pulse audio
pulseaudio -D --exit-idle-time=-1 
# Create a virtual speaker output
pactl load-module module-null-sink sink_name=SpeakerOutput sink_properties=device.description="Dummy_Output"
# Create a virtual microphone
pacmd load-module module-virtual-source source_name=VirtualMicrophone

# Stand up a local server that serves the media files within opt/media
python3 -m SimpleHTTPServer &>/dev/null

# # Start chromium
# while true
# do 
#   python3 main.py -c ${CHANNEL} -u ${USER} -p ${PASS}
#   sleep 2
# done &

# supervisor
/usr/bin/supervisord --configuration /etc/supervisord.conf &

SUPERVISOR_PID=$!

function shutdown {
    echo "Trapped SIGTERM/SIGINT/x so shutting down supervisord..."
    kill -s SIGTERM ${SUPERVISOR_PID}
    wait ${SUPERVISOR_PID}
    echo "Shutdown complete"
}

trap shutdown SIGTERM SIGINT
wait ${SUPERVISOR_PID}
