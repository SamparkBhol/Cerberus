from django.db import models

class TrafficLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    source_ip = models.CharField(max_length=50)
    dest_ip = models.CharField(max_length=50)
    source_port = models.IntegerField()
    dest_port = models.IntegerField()
    protocol = models.CharField(max_length=10)
    packet_size = models.IntegerField()
    tcp_flags = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.source_ip}:{self.source_port} -> {self.dest_ip}:{self.dest_port}"

class Alert(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=255)
    severity = models.CharField(max_length=20, default="Low")
    traffic_log = models.ForeignKey(TrafficLog, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"[{self.timestamp}] {self.message}"
