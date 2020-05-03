# pyopenvpn-monitor
Use this bot to track the status of the running OpenVPN server.</br>
Provide a bot's token, a list of allowed users and a path the openvpn-status.log file and that's it.<br/>
<br/>
<b>Build a docker image:</b><br/>
docker build -t pyopenvpn-monitor:v0.1 . <br/>
<br/>
<b>Start the container and mount the OpenVPN status file:</b><br/>
docker run --rm -it --mount type=bind,source=/etc/openvpn/openvpn-status.log,target=/ovpn-bot/openvpn-status.log pyopenvpn-monitor:v0.1<br/>
