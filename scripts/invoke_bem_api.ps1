
netstat -a|findstr "48884"
#   TCP    0.0.0.0:48884          Dormitorio:0           LISTENING

Invoke-RestMethod -Uri "http://localhost:48884/bem_api/process" -Method Post -ContentType "application/json" -Body '{"message": "Testing pyRevit Routes!"}'