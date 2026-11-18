import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private urlBase = 'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  private obtenerCabeceras(): HttpHeaders {
    const token = localStorage.getItem('token_aegisart') || '';
    let headers = new HttpHeaders();
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  }

  guardarSesion(token: string, usuario: any): void {
    localStorage.setItem('token_aegisart', token);
    localStorage.setItem('usuario_aegisart', JSON.stringify(usuario));
  }

  obtenerUsuarioLocal(): any {
    const raw = localStorage.getItem('usuario_aegisart');
    if (raw) {
      try { return JSON.parse(raw); } catch { return null; }
    }
    return null;
  }

  cerrarSesion(): void {
    localStorage.removeItem('token_aegisart');
    localStorage.removeItem('usuario_aegisart');
  }

  // ================= US-01 y US-07: AUTENTICACIÓN Y PERFIL =================
  registrarUsuario(datos: any): Observable<any> {
    return this.http.post(`${this.urlBase}/autenticacion/registro`, datos);
  }

  iniciarSesion(datos: any): Observable<any> {
    return this.http.post(`${this.urlBase}/autenticacion/iniciar-sesion`, datos);
  }

  solicitarRecuperacion(correo: string): Observable<any> {
    return this.http.post(`${this.urlBase}/autenticacion/recuperar-cuenta`, { correo });
  }

  restablecerContrasena(datos: any): Observable<any> {
    return this.http.post(`${this.urlBase}/autenticacion/restablecer-contrasena`, datos);
  }

  obtenerPerfil(): Observable<any> {
    return this.http.get(`${this.urlBase}/autenticacion/perfil`, { headers: this.obtenerCabeceras() });
  }

  actualizarPerfil(datos: any): Observable<any> {
    return this.http.put(`${this.urlBase}/autenticacion/perfil`, datos, { headers: this.obtenerCabeceras() });
  }

  // ================= US-02, US-03, US-04, US-08, US-09: OBRAS =================
  obtenerResumenInicio(): Observable<any> {
    return this.http.get(`${this.urlBase}/obras/resumen-inicio`, { headers: this.obtenerCabeceras() });
  }

  listarObras(buscar: string = '', filtroEstado: string = 'Todas'): Observable<any[]> {
    const params = `?buscar=${encodeURIComponent(buscar)}&filtro_estado=${encodeURIComponent(filtroEstado)}`;
    return this.http.get<any[]>(`${this.urlBase}/obras${params}`, { headers: this.obtenerCabeceras() });
  }

  listarCatalogoInspiracion(): Observable<any[]> {
    return this.http.get<any[]>(`${this.urlBase}/obras/catalogo-inspiracion`);
  }

  protegerYRegistrarObra(formData: FormData): Observable<any> {
    return this.http.post(`${this.urlBase}/obras/proteger-y-registrar`, formData, {
      headers: this.obtenerCabeceras()
    });
  }

  obtenerDetalleObra(obraId: number): Observable<any> {
    return this.http.get(`${this.urlBase}/obras/${obraId}`, { headers: this.obtenerCabeceras() });
  }

  // ================= US-05 y US-11: MONITOREO POR URL, COINCIDENCIAS Y PDF =================
  obtenerEstadoMonitoreo(): Observable<any> {
    return this.http.get(`${this.urlBase}/monitoreo/estado`, { headers: this.obtenerCabeceras() });
  }

  escanearUrlTemporal(urlTemporal: string, obraId?: number | null): Observable<any> {
    const payload: any = { url_temporal: urlTemporal };
    if (obraId) payload.obra_id = Number(obraId);
    return this.http.post(`${this.urlBase}/monitoreo/escanear-url`, payload, {
      headers: this.obtenerCabeceras()
    });
  }

  listarCoincidencias(filtro: string = 'Todas'): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.urlBase}/monitoreo/coincidencias?filtro=${encodeURIComponent(filtro)}`,
      { headers: this.obtenerCabeceras() }
    );
  }

  obtenerDetalleCoincidencia(coincidenciaId: number): Observable<any> {
    return this.http.get(`${this.urlBase}/monitoreo/coincidencias/${coincidenciaId}`, {
      headers: this.obtenerCabeceras()
    });
  }

  actualizarEstadoCoincidencia(coincidenciaId: number, estadoArtista: string): Observable<any> {
    return this.http.put(
      `${this.urlBase}/monitoreo/coincidencias/${coincidenciaId}/estado`,
      { estado_artista: estadoArtista },
      { headers: this.obtenerCabeceras() }
    );
  }

  obtenerUrlDescargaPdf(coincidenciaId: number): string {
    return `${this.urlBase}/monitoreo/coincidencias/${coincidenciaId}/descargar-reporte-pdf`;
  }

  // ================= US-06: PLANES DE SUSCRIPCIÓN =================
  listarPlanes(buscar: string = '', estado: string = 'Todos los estados', periodicidad: string = 'Todas las periodicidades'): Observable<any[]> {
    const q = `?buscar=${encodeURIComponent(buscar)}&estado=${encodeURIComponent(estado)}&periodicidad=${encodeURIComponent(periodicidad)}`;
    return this.http.get<any[]>(`${this.urlBase}/planes${q}`);
  }

  crearPlan(datos: any): Observable<any> {
    return this.http.post(`${this.urlBase}/planes`, datos);
  }

  actualizarPlan(planId: number, datos: any): Observable<any> {
    return this.http.put(`${this.urlBase}/planes/${planId}`, datos);
  }

  // ================= US-09, US-10 y US-12: MODERACIÓN Y MÉTRICAS DUEÑO =================
  obtenerCasosModeracion(): Observable<any> {
    return this.http.get(`${this.urlBase}/moderacion-admin/casos`);
  }

  resolverCasoModerador(casoId: number, decision: string, comentarios: string): Observable<any> {
    return this.http.put(`${this.urlBase}/moderacion-admin/casos/${casoId}/resolver`, {
      decision,
      comentarios
    });
  }

  revisarObraSospechosa(obraId: number, decision: string, comentarios: string): Observable<any> {
    return this.http.put(`${this.urlBase}/moderacion-admin/obras-sospechosas/${obraId}/revisar`, {
      decision,
      comentarios
    });
  }

  obtenerMetricasDueno(): Observable<any> {
    return this.http.get(`${this.urlBase}/moderacion-admin/metricas-dueno`);
  }

  obtenerMetricasIaApf3(): Observable<any> {
    return this.http.get(`${this.urlBase}/moderacion-admin/metricas-ia-apf3`);
  }
}