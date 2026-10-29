- last 30 logs
```
sudo tail -30 /var/log/auth.log
```

- file all logs
```
sudo cat /var/log/auth.log
```

- for start services (Linux server)
```
sudo systemctl start elasticsearch
sudo systemctl start kibana
sudo systemctl start filebeat
```

- check services (linux server)
```
systemctl status elasticsearch kibana filebeat
```

- extra start (if need) (Linux server)
```
ssh -L 5601:127.0.0.1:5601 NAME@SERVER_IP
```