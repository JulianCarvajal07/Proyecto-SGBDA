from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from sgbda.utils.fields import EncryptedPasswordField
from django.core.exceptions import ValidationError
 

class UsuarioManager(BaseUserManager):
    def create_user(self, nombre, password=None, **extra_fields):
        user = self.model(nombre=nombre, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, nombre, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        return self.create_user(nombre, password, **extra_fields)

class usuario(AbstractBaseUser, PermissionsMixin):
    nombre = models.CharField(max_length=150, unique=True)
    rol = models.CharField(max_length=50, blank=True, default='')


    is_active = models.BooleanField(default=True)
    is_staff  = models.BooleanField(default=False)  # Solo para el admin de Django

    objects = UsuarioManager()

    # REQUIRED_FIELDS es necesario para crear superusuarios por consola
    # ejemplo python manage.py createsuperuser
    # con el super usuario se puede ingresar al panel admin de django http://localhost:8000/admin/
    USERNAME_FIELD = 'nombre'
    REQUIRED_FIELDS = ['rol']  # ✅

class cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cliente'

    def __str__(self):
        return self.nombre
    

class servidor(models.Model):
    id_servidor = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        cliente,
        on_delete=models.CASCADE,
        db_column='cliente_id',
        null=True,
        blank=True
    )
    ip = models.GenericIPAddressField(unique=True)
    hostname = models.CharField(max_length=255)
    sistema_operativo = models.CharField(max_length=100)

    class Meta:
        db_table = 'servidor'

    def __str__(self):
        return self.hostname
    

class instancia(models.Model):
    id_instancia = models.AutoField(primary_key=True)
    servidor = models.ForeignKey(
        servidor,
        on_delete=models.CASCADE,
        db_column='servidor_id',
    )
    nombre_instancia = models.CharField(max_length=255)
    puerto = models.CharField(max_length=50)
    build = models.CharField(max_length=500, null=True, blank=True) #temporal
    major_version = models.CharField(max_length=50)
    edition = models.CharField(max_length=100)
    observaciones = models.TextField(blank=True, default="")
    administrado = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = 'instancia'

    def __str__(self):
        return self.nombre_instancia


class conexion(models.Model):
    motor = models.CharField(max_length=70, blank=True, null=True)
    ip_servidor = models.GenericIPAddressField()
    puerto = models.CharField(max_length=50)
    tipo_autenticacion = models.CharField(max_length=100)
    usuario = models.CharField(max_length=255)
    password_encriptado = EncryptedPasswordField()

    class Meta:
        db_table = 'conexion'

    def __str__(self):
        return f"Conexion {self.id_conexion} - {self.instancia}"
    
#================================================================
#================================================================
#================================================================
#================================================================

class servicio(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    instancia = models.ForeignKey(
        instancia,
        on_delete=models.CASCADE,
        db_column='instancia_id',
        related_name='servicios'
    )
    nombre_servicio = models.CharField(max_length=255)
    estado_servicio = models.CharField(max_length=100)
    tipo_inicio = models.CharField(max_length=100, null=True, blank=True)
    ultima_verificacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'servicio'

    def __str__(self):
        return self.nombre_servicio


class checkSQL(models.Model):
    id_check = models.AutoField(primary_key=True)
    instancia = models.ForeignKey(
        instancia,
        on_delete=models.CASCADE,
        db_column='instancia_id',
        related_name='checksql'
    )
    build_detectado = models.CharField(max_length=100)
    build_referencia = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    fecha_publicacion = models.DateField(null=True, blank= True)
    nombre_ultima_update = models.CharField(max_length=200, null=True, blank=True)
    fecha_check = models.DateTimeField()
    detalle = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'check_sql'

    def __str__(self):
        return f"Check {self.id_check} - {self.instancia}"


class actualizaciones(models.Model):
    id_actualizaciones = models.AutoField(primary_key=True)
    motor = models.CharField(max_length=60, null=True, blank=True)
    major_version = models.CharField(max_length=50) # Guarda la versión principal de SQL Server.
    build = models.CharField(max_length=200)  # Guarda el número oficial del build publicado por Microsoft.
    kb = models.CharField(max_length=150) # Es el identificador oficial del parche/documentación Microsoft.
    descripcion = models.TextField() # Texto descriptivo de la actualización.
    release_date = models.DateField(null=True, blank=True) # Fecha oficial de publicación del GDR.
    #soportado = models.BooleanField(default=True) # Indica si la versión/build todavía está soportada.
    fecha_registro = models.DateTimeField(auto_now_add=True) # Fecha en la que el sistema guardó/sincronizó ese registro

    class Meta:
        db_table = 'actualizaciones'

    def __str__(self):
        return f"{self.major_version} - {self.cu}"
    
#================================================================
#================================================================
#================================================================
#================================================================

class Asignacion(models.Model):
    """
    Registra trabajos asignados a clientes en una fecha concreta.
    Dos tipos:
      - mantenimiento: mantenimiento mensual registrado manualmente cada mes
      - soporte: trabajo esporadico
    Cada registro representa un hecho puntual, no una regla recurrente.
    """

    MOTIVO_CHOICES = [
        ('mantenimiento', 'Mantenimiento mensual'),
        ('soporte', 'Soporte esporadico'),
    ]

    cliente = models.ForeignKey(
        cliente,
        on_delete=models.CASCADE,
        related_name='asignaciones',
        verbose_name='cliente'
    )

    motivo = models.CharField(
        max_length=20,
        choices=MOTIVO_CHOICES,
        verbose_name='motivo'
    )

    fecha_exacta = models.DateField(
        verbose_name='fecha exacta'
    )

    class Meta:
        db_table = 'asignacion'
        verbose_name = 'asignacion'
        verbose_name_plural = 'asignaciones'
        indexes = [
            models.Index(fields=['cliente', 'motivo']),
            models.Index(fields=['motivo', 'fecha_exacta']),
        ]

    def __str__(self):
        return f"{self.cliente} - {self.get_motivo_display()} {self.fecha_exacta}"