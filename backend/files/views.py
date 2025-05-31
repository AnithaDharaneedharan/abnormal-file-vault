from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import File
from .serializers import FileSerializer
import hashlib

# Create your views here.

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer

    def calculate_file_hash(self, file):
        """Calculate SHA-256 hash of file contents"""
        sha256 = hashlib.sha256()
        for chunk in file.chunks():
            sha256.update(chunk)
        return sha256.hexdigest()

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate file hash
        file_hash = self.calculate_file_hash(file_obj)
        
        # Check if file with same hash exists
        existing_file = File.objects.filter(file_hash=file_hash).first()
        if existing_file:
            return Response(
                {
                    'error': 'Duplicate file',
                    'message': 'This file has already been uploaded.',
                    'existing_file': self.get_serializer(existing_file).data
                },
                status=status.HTTP_409_CONFLICT
            )
        
        # Reset file pointer after hash calculation
        file_obj.seek(0)
        
        data = {
            'file': file_obj,
            'original_filename': file_obj.name,
            'file_type': file_obj.content_type,
            'size': file_obj.size,
            'file_hash': file_hash
        }
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
