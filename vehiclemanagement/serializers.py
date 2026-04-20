from rest_framework import serializers
from .models import TravelTrip


# ── Helpers ───────────────────────────────────────────────────────────────────

VALID_SERVICES = {'washing', 'alignment', 'airChecking', 'greaseOil'}


def _parse_services(value):
    """Accept a list OR a comma-separated string; return a cleaned comma string."""
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [s.strip() for s in value.split(',') if s.strip()]
    else:
        items = []
    invalid = set(items) - VALID_SERVICES
    if invalid:
        raise serializers.ValidationError(
            f"Invalid service(s): {', '.join(invalid)}. "
            f"Allowed: {', '.join(sorted(VALID_SERVICES))}"
        )
    return ','.join(items)


# ── List / Table serializer (read-only, matches Travel_Trip.jsx table columns) ─

class TravelTripListSerializer(serializers.ModelSerializer):
    """Lightweight serializer used for the trip table view."""

    services_list = serializers.SerializerMethodField()
    start_img_url = serializers.SerializerMethodField()
    end_img_url   = serializers.SerializerMethodField()

    class Meta:
        model = TravelTrip
        fields = [
            'id',
            'vehicle_name',
            'registration_number',
            'traveled_by',
            'purpose_of_trip',
            'date',
            'start_time',
            'end_date',
            'end_time',
            'odometer_start',
            'odometer_end',
            'distance_covered',
            'fuel_cost',
            'maintenance_cost',
            'status',
            'services_list',
            'start_img_url',
            'end_img_url',
            'created_at',
        ]
        read_only_fields = fields

    def get_services_list(self, obj):
        if not obj.services:
            return []
        return [s.strip() for s in obj.services.split(',') if s.strip()]

    def get_start_img_url(self, obj):
        request = self.context.get('request')
        if obj.odometer_start_image and request:
            return request.build_absolute_uri(obj.odometer_start_image.url)
        return None

    def get_end_img_url(self, obj):
        request = self.context.get('request')
        if obj.odometer_end_image and request:
            return request.build_absolute_uri(obj.odometer_end_image.url)
        return None


# ── Start-Trip serializer (maps to StartTrip.jsx payload) ────────────────────

class StartTripSerializer(serializers.ModelSerializer):
    """
    Accepts the payload sent by StartTrip.jsx:
      vehicle_id, vehicle_name, registration_number, date, time,
      purpose_of_trip, traveled_by, maintenance_cost,
      odometer_start, services (list), odometer_image (file)

    FIX: traveled_by and odometer_start are now explicitly declared so they
    are accepted from the frontend and persisted to the database.
    """

    # The frontend sends "time" for start_time
    time = serializers.TimeField(source='start_time', required=True)

    # The frontend sends a list for services
    services = serializers.ListField(
        child=serializers.ChoiceField(choices=list(VALID_SERVICES)),
        required=False,
        default=list,
        write_only=True,
    )

    # The frontend sends "odometer_image" for the start-odometer photo
    odometer_image = serializers.ImageField(
        source='odometer_start_image', required=False, allow_null=True
    )

    class Meta:
        model = TravelTrip
        fields = [
            'id',
            'vehicle_name',
            'registration_number',
            # FIX 1: include traveled_by so the driver's name is saved
            'traveled_by',
            'date',
            'time',              # → start_time
            'purpose_of_trip',
            'maintenance_cost',
            # FIX 2: include odometer_start so distance can be computed on end
            'odometer_start',
            'services',
            'odometer_image',    # → odometer_start_image
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']
        extra_kwargs = {
            'vehicle_name':   {'required': True},
            # FIX 1: traveled_by is optional (falls back to empty string)
            'traveled_by':    {'required': False, 'default': ''},
            # FIX 2: odometer_start is optional at start time
            'odometer_start': {'required': False, 'allow_null': True},
        }

    def validate_services(self, value):
        return value  # already validated by ChoiceField children

    def create(self, validated_data):
        services_list = validated_data.pop('services', [])
        validated_data['services'] = ','.join(services_list)
        validated_data['status']   = 'ongoing'
        return super().create(validated_data)

    def to_representation(self, instance):
        data = TravelTripListSerializer(instance, context=self.context).data
        return data


# ── End-Trip serializer (maps to EndTrip.jsx payload) ────────────────────────

class EndTripSerializer(serializers.ModelSerializer):
    """
    Accepts PATCH payload sent by EndTrip.jsx:
      fuel_cost, end_time, odometer_end, odometer_image (end photo)
    """

    odometer_image = serializers.ImageField(
        source='odometer_end_image', required=False, allow_null=True
    )

    class Meta:
        model = TravelTrip
        fields = [
            'id',
            'end_date',
            'end_time',
            'odometer_end',
            'fuel_cost',
            'odometer_image',    # → odometer_end_image
            'distance_covered',  # read-only (auto-computed in model.save)
            'status',
            'updated_at',
        ]
        read_only_fields = ['id', 'distance_covered', 'status', 'updated_at']

    def validate(self, attrs):
        instance = self.instance
        odo_end = attrs.get('odometer_end')
        if odo_end is not None and instance and instance.odometer_start is not None:
            if float(odo_end) < float(instance.odometer_start):
                raise serializers.ValidationError({
                    'odometer_end': (
                        f"End reading ({odo_end}) must be ≥ "
                        f"start reading ({instance.odometer_start}) km."
                    )
                })
        return attrs

    def to_representation(self, instance):
        return TravelTripListSerializer(instance, context=self.context).data