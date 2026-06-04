# views.py
import queue
import threading
from django.http import StreamingHttpResponse
from django.views.decorators.http import require_GET
from sgbda.services.actualizar_instancias_v3 import actualizar_instancias_desde_conexiones

def stream_actualizacion(request):
    log_queue = queue.Queue()

    def run():
        try:
            actualizar_instancias_desde_conexiones(log_queue)
        finally:
            log_queue.put(None)  # señal de fin

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    def event_stream():
        while True:
            mensaje = log_queue.get()
            if mensaje is None:
                yield "event: fin\ndata: Proceso completado\n\n"
                break
            yield f"data: {mensaje}\n\n"

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # importante para nginx
    return response