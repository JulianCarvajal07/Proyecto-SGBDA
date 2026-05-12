from django.db import models


class cliente(models.Model):
    id_cliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    estado = models.CharField(max_length=100)
    fecha_creacion = models.DateField()

    class Meta:
        db_table = 'cliente'

    def __str__(self):
        return self.nombre


class usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return self.nombre


class servidor(models.Model):
    id_servidor = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        cliente,
        on_delete=models.CASCADE,
        db_column='cliente_id'
    )
    hostname = models.CharField(max_length=255)
    ip = models.GenericIPAddressField()
    sistema_operativo = models.CharField(max_length=100)
    fecha_registro = models.DateField()

    class Meta:
        db_table = 'servidor'

    def __str__(self):
        return self.hostname


class instancia(models.Model):
    id_instancia = models.AutoField(primary_key=True)
    servidor = models.ForeignKey(
        servidor,
        on_delete=models.CASCADE,
        db_column='servidor_id'
    )
    nombre_instancia = models.CharField(max_length=255)
    puerto = models.IntegerField()
    major_version = models.CharField(max_length=50)
    edition = models.CharField(max_length=100)

    class Meta:
        db_table = 'instancia'

    def __str__(self):
        return self.nombre_instancia


class conexion(models.Model):
    id_conexion = models.AutoField(primary_key=True)
    instancia = models.ForeignKey(
        instancia,
        on_delete=models.CASCADE,
        db_column='instancia_id'
    )
    tipo_autenticacion = models.CharField(max_length=100)
    usuario = models.CharField(max_length=255)
    password_encriptado = models.CharField(max_length=512)

    class Meta:
        db_table = 'conexion'

    def __str__(self):
        return f"Conexion {self.id_conexion} - {self.instancia}"


class servicio(models.Model):
    id_servicio = models.AutoField(primary_key=True)
    instancia = models.ForeignKey(
        instancia,
        on_delete=models.CASCADE,
        db_column='instancia_id'
    )
    nombre_servicio = models.CharField(max_length=255)
    estado_servicio = models.CharField(max_length=100)
    ultima_verificacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'servicio'

    def __str__(self):
        return self.nombre_servicio


class checkSQL(models.Model):
    id_check = models.AutoField(primary_key=True)
    instancia = models.ForeignKey(
        instancia,
        on_delete=models.CASCADE,
        db_column='instancia_id'
    )
    build_detectado = models.CharField(max_length=100)
    build_referencia = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    fecha_check = models.DateTimeField()
    detalle = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'check_sql'

    def __str__(self):
        return f"Check {self.id_check} - {self.instancia}"


class actualizaciones(models.Model):
    id_actualizaciones = models.AutoField(primary_key=True)
    major_version = models.CharField(max_length=50)
    cu = models.CharField(max_length=100)
    kb = models.CharField(max_length=100)
    release_date = models.DateField(null=True, blank=True)
    soportado = models.BooleanField(default=True)
    fecha = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'actualizaciones'

    def __str__(self):
        return f"{self.major_version} - {self.cu}"