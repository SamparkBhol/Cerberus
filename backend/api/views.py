from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .serializers import UserSerializer, RegisterSerializer, TrafficLogSerializer, AlertSerializer
from .models import TrafficLog, Alert
from .ml_model import detector
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
import threading
from django.db import transaction

logger = logging.getLogger(__name__)

training_packets_buffer = []
training_in_progress = False
TRAINING_SET_SIZE = 100
training_lock = threading.Lock()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class AlertListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AlertSerializer
    
    def get_queryset(self):
        return Alert.objects.all().order_by('-timestamp')[:50]

class StatsView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        from django.db.models import Count
        
        protocol_breakdown = (
            TrafficLog.objects.values('protocol')
            .annotate(count=Count('protocol'))
            .order_by('-count')
        )
        
        top_sources = (
            TrafficLog.objects.values('source_ip')
            .annotate(count=Count('source_ip'))
            .order_by('-count')[:10]
        )
        
        return Response({
            'protocol_breakdown': list(protocol_breakdown),
            'top_sources': list(top_sources)
        })

class ModelTrainingView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        global training_in_progress, training_packets_buffer, training_lock
        
        with training_lock:
            if training_in_progress:
                return Response({'message': 'Training already in progress'}, status=status.HTTP_400_BAD_REQUEST)
            
            training_in_progress = True
            training_packets_buffer = []
        
        logger.info(f"Starting training mode... collecting {TRAINING_SET_SIZE} packets.")
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'traffic_group',
            {
                'type': 'system_message',
                'message': f'Starting ML model training. Collecting {TRAINING_SET_SIZE} packets for baseline...'
            }
        )
        
        return Response({'message': 'Training started. Collecting baseline packets.'})

    def get(self, request, *args, **kwargs):
        return Response({
            'is_trained': detector.is_trained,
            'is_training': training_in_progress
        })

def process_and_broadcast(packets):
    global training_in_progress, training_packets_buffer, training_lock, detector
    
    channel_layer = get_channel_layer()
    anomalous_packets = []
    saved_logs = []

    try:
        with transaction.atomic():
            for packet_data in packets:
                serializer = TrafficLogSerializer(data=packet_data)
                if serializer.is_valid():
                    log_entry = serializer.save()
                    saved_logs.append(serializer.data)
                else:
                    logger.warning(f"Invalid packet data received: {serializer.errors}")
    except Exception as e:
        logger.error(f"Error during database transaction: {e}")
        return

    with training_lock:
        if training_in_progress:
            training_packets_buffer.extend(packets)
            logger.debug(f"Collected {len(training_packets_buffer)}/{TRAINING_SET_SIZE} training packets.")
            
            if len(training_packets_buffer) >= TRAINING_SET_SIZE:
                logger.info("Sufficient packets collected, starting model training in background.")
                buffer_copy = list(training_packets_buffer)
                training_packets_buffer = []
                training_in_progress = False
                
                def train_thread():
                    global detector, training_in_progress
                    logger.info(f"Training thread started with {len(buffer_copy)} packets.")
                    success = detector.train(buffer_copy)
                    message = "Model training complete and is now active." if success else "Model training failed. Please check logs."
                    logger.info(message)
                    async_to_sync(channel_layer.group_send)(
                        'traffic_group',
                        {'type': 'system_message', 'message': message}
                    )
                
                threading.Thread(target=train_thread).start()
        
        elif detector.is_trained:
            anomalous_packets, anomalous_indices = detector.predict(packets)
            
            for i in anomalous_indices:
                try:
                    log_entry = TrafficLog.objects.get(id=saved_logs[i]['id'])
                    message = f"Anomaly detected: Unusual traffic from {log_entry.source_ip}:{log_entry.source_port} to {log_entry.dest_ip}:{log_entry.dest_port} ({log_entry.protocol})"
                    
                    alert_serializer = AlertSerializer(data={'message': message, 'traffic_log': log_entry.id})
                    if alert_serializer.is_valid():
                        alert_entry = alert_serializer.save()
                        async_to_sync(channel_layer.group_send)(
                            'traffic_group',
                            {
                                'type': 'new_alert',
                                'alert': alert_serializer.data
                            }
                        )
                except Exception as e:
                    logger.error(f"Error creating alert: {e}")

    for log_data in saved_logs:
        async_to_sync(channel_layer.group_send)(
            'traffic_group',
            {
                'type': 'new_traffic',
                'traffic': log_data
            }
        )

class IngestView(APIView):
    permission_classes = (permissions.AllowAny,) 

    def post(self, request, *args, **kwargs):
        packets = request.data.get('packets')
        if not packets or not isinstance(packets, list):
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        
        threading.Thread(target=process_and_broadcast, args=(packets,)).start()
        
        return Response({'message': 'Data received'}, status=status.HTTP_202_ACCEPTED)