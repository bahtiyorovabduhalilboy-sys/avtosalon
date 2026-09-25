from rest_framework import serializers
from django.utils import timezone
from .models import *
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = '__all__'

    def validate_year(self, value):
        current_year = timezone.now().year
        if value < 1886 or value > current_year + 1:
            raise serializers.ValidationError("Chiqarilgan yil noto'g'ri kiritilgan.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Narx musbat son bo'lishi kerak.")
        return value

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = '__all__'

    def validate_car(self, value):
        if not value.available:
            raise serializers.ValidationError("Ushbu mashina allaqachon sotilgan yoki mavjud emas!")
        return value
class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = '__all__'
class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ['id', 'username', 'full_name', 'phone_number', 'photo', 'salary', 'position']
        extra_kwargs = {'password': {'write_only': True}}

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Worker
        fields = ['id', 'username', 'email', 'password', 'full_name', 'phone_number', 'position']

    def create(self, validated_data):
        user = Worker.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('full_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            position=validated_data.get('position', None)
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Foydalanuvchi nomi yoki parol noto'g'ri!")
        
        refresh = RefreshToken.for_user(user)
        return {
            'username': user.username,
            'email': user.email,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except Exception:
            raise serializers.ValidationError("Token yaroqsiz yoki allaqachon bekor qilingan.")

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not Worker.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ushbu email bilan ro'yxatdan o'tgan foydalanuvchi topilmadi.")
        return value

    def send_reset_email(self):
        email = self.validated_data['email']
        user = Worker.objects.get(email=email)
        
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        reset_link = f"http://127.0.0.1:8000/api/password-reset-confirm/{uid}/{token}/"
        
        subject = "Parolni tiklash - Avtosalon API"
        message = f"Salom {user.username},\n\nParolingizni tiklash uchun quyidagi havolaga bosing:\n{reset_link}\n\nAgar bu so'rovni siz yubormagan bo'lsangiz, xabarni e'tiborsiz qoldiring."
        
        send_mail(subject, message, None, [email])

class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)

    def save_new_password(self, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = Worker.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Worker.DoesNotExist):
            raise serializers.ValidationError("Yaroqsiz UID")

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            raise serializers.ValidationError("Token yaroqsiz yoki muddati o'tgan")

        user.set_password(self.validated_data['new_password'])
        user.save()
        return user