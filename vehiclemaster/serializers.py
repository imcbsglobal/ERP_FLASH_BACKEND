from rest_framework import serializers
from .models import VehicleMaster


class VehicleMasterSerializer(serializers.ModelSerializer):

    class Meta:
        model = VehicleMaster
        fields = [
            'id',
            'vehicle_name',
            'company_brand',
            'registration_number',
            'vehicle_type',
            'ownership',
            'fuel_type',
            'vehicle_photo',
            'owner_name',
            'insurance_no',
            'insurance_expired_date',
            'pollution_expired_date',
            'last_service_date',
            'next_service_date',
            'current_odometer',
            'chassis_number',
            'engine_number',
            'note',
            'status',
            'total_trips',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'total_trips', 'created_at', 'updated_at']