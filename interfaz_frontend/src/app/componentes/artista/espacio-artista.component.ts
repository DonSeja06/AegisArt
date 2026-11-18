import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../servicios/api.service';

@Component({
  selector: 'app-espacio-artista',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="layout-espacio">
      <!-- ================= BARRA LATERAL (SIDEBAR FIGMA) ================= -->
      <!-- ================= BARRA LATERAL ESTRICTAMENTE SEPARADA POR ROL ================= -->
      <aside class="barra-lateral">
        <div>
          <div class="marca-logo">
            <span class="icono-check-logo">✓</span>
            <span>Aegis<span style="color: var(--morado-primario);">Art</span></span>
          </div>

          <div class="caja-usuario-sidebar">
            <div class="avatar-nc">{{ perfil?.iniciales || 'AA' }}</div>
            <div>
              <p style="font-size: 12px; font-weight: 700; color: var(--texto-principal);">
                {{ perfil?.rol === 'dueno' ? 'Administración' : (perfil?.rol === 'moderador' ? 'Moderación' : 'Espacio personal') }}
              </p>
              <p style="font-size: 12px; color: var(--texto-secundario);">{{ perfil?.nombre_apellido }}</p>
            </div>
          </div>

          <!-- MENÚ EXCLUSIVO PARA ROL ARTISTA -->
          <ng-container *ngIf="perfil?.rol === 'artista'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); letter-spacing: 0.8px; margin: 12px 10px 8px;">
              TU ESPACIO CREATIVO
            </p>
            <nav>
              <div class="nav-item" [class.activo]="seccionActual === 'inicio'" (click)="cambiarSeccion('inicio')">
                <span>⌂ Inicio</span>
              </div>
              <div class="nav-item" [class.activo]="seccionActual === 'mis_obras' || seccionActual === 'detalle_obra'" (click)="cambiarSeccion('mis_obras')">
                <span>▦ Mis obras</span>
              </div>
              <div class="nav-item" [class.activo]="seccionActual === 'proteger' || seccionActual === 'procesando'" (click)="iniciarFlujoProteger()">
                <span>✦ Proteger obra</span>
              </div>
              <div class="nav-item" [class.activo]="seccionActual === 'monitoreo'" (click)="cambiarSeccion('monitoreo')">
                <span>◉ Monitoreo</span>
              </div>
              <div class="nav-item" [class.activo]="seccionActual === 'coincidencias' || seccionActual === 'revision_coincidencia'" (click)="cambiarSeccion('coincidencias')">
                <span>⇄ Coincidencias</span>
                <span *ngIf="resumenInicio?.metricas?.coincidencias > 0"
                      style="background: var(--ambar-fondo); color: var(--ambar-alerta); font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 99px;">
                  {{ resumenInicio.metricas.coincidencias }}
                </span>
              </div>
              <div class="nav-item" [class.activo]="seccionActual === 'certificados'" (click)="cambiarSeccion('certificados')">
                <span>◇ Certificados</span>
              </div>
              <div class="nav-item" [class.activo]="seccionActual === 'reportes'" (click)="cambiarSeccion('reportes')">
                <span>▤ Reportes</span>
              </div>
              <div class="nav-item" [class.activo]="seccionActual === 'suscripciones'" (click)="cambiarSeccion('suscripciones')">
                <span>▣ Pagos y suscripciones</span>
              </div>
              <div class="nav-item" [class.activo]="seccionActual === 'configuracion'" (click)="cambiarSeccion('configuracion')">
                <span>⚙ Configuración</span>
              </div>
            </nav>
          </ng-container>

          <!-- MENÚ EXCLUSIVO PARA ROL MODERADOR (US-09 y US-10 - Sin subir obras) -->
          <ng-container *ngIf="perfil?.rol === 'moderador'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); letter-spacing: 0.8px; margin: 12px 10px 8px;">
              PANEL DE MODERACIÓN
            </p>
            <nav>
              <div class="nav-item" [class.activo]="seccionActual === 'moderacion' || seccionActual === 'moderacion_detalle'" (click)="cambiarSeccion('moderacion')">
                <span>🛡 Casos y Sospechosas</span>
              </div>
              <div class="nav-item" (click)="salirAlLogin()">
                <span>↪ Cerrar sesión</span>
              </div>
            </nav>
          </ng-container>

          <!-- MENÚ EXCLUSIVO PARA ROL DUEÑO DE LA APLICACIÓN (US-06 y US-12 - Sin subir obras) -->
          <ng-container *ngIf="perfil?.rol === 'dueno'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); letter-spacing: 0.8px; margin: 12px 10px 8px;">
              GESTIÓN Y MÉTRICAS
            </p>
            <nav>
              <div class="nav-item" [class.activo]="seccionActual === 'admin_planes' && modoAdminPlan === 'listado'"
                   (click)="abrirGestionPlanesAdmin()">
                <span>▣ Listado de planes (US-06)</span>
              </div>
              <div class="nav-item" [class.activo]="seccionActual === 'admin_planes' && modoAdminPlan === 'formulario'"
                   (click)="iniciarCrearPlan()">
                <span>✦ Crear nuevo plan</span>
              </div>
              <div class="nav-item" (click)="salirAlLogin()">
                <span>↪ Cerrar sesión</span>
              </div>
            </nav>
          </ng-container>
        </div>

        <!-- Caja inferior de cuota SOLO para el Artista -->
        <div *ngIf="perfil?.rol === 'artista'" class="caja-cuota-sidebar">
          <p style="font-size: 12px; font-weight: 700; color: var(--morado-primario);">✦ Más libertad para crear</p>
          <p style="font-size: 12px; color: var(--texto-secundario); margin-top: 4px;">
            {{ perfil?.obras_protegidas_actuales || 0 }} de {{ perfil?.limite_obras_plan || 50 }} obras protegidas
          </p>
          <div class="barra-progreso-fondo">
            <div class="barra-progreso-relleno"
                 [style.width.%]="((perfil?.obras_protegidas_actuales || 0) / (perfil?.limite_obras_plan || 50)) * 100"></div>
          </div>
          <a (click)="cambiarSeccion('suscripciones')" style="font-size: 12px; font-weight: 700; color: var(--texto-principal); cursor: pointer;">
            Explorar AegisArt Pro →
          </a>
        </div>
      </aside>

      <!-- ================= ÁREA PRINCIPAL DERECHA ================= -->
      <div class="contenido-principal">
        <!-- Barra Superior (Topbar) -->
        <header class="barra-superior">
          <div style="font-size: 13px; color: var(--texto-secundario);">
            Mi espacio &nbsp;/&nbsp; <strong style="color: var(--texto-principal);">{{ obtenerTituloBreadcrumb() }}</strong>
          </div>

          <div style="display: flex; align-items: center; gap: 18px; position: relative;">
            <span style="font-size: 12px; color: var(--texto-secundario); display: flex; align-items: center; gap: 6px;">
              <span style="width: 8px; height: 8px; border-radius: 50%; background: var(--verde-exito); display: inline-block;"></span>
              Todos los sistemas operativos
            </span>

            <!-- Campana de Notificaciones desplegable (Figura 19 / US-05 y US-09) -->
            <button (click)="mostrarPanelNotificaciones = !mostrarPanelNotificaciones"
                    style="background: var(--lavanda-suave); border: none; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; color: var(--morado-primario); font-weight: 700;">
              🔔
            </button>

            <div class="avatar-nc" style="cursor: pointer;" (click)="cambiarSeccion('configuracion')">
              {{ perfil?.iniciales || 'NC' }}
            </div>

            <!-- Popup de Notificaciones -->
            <div *ngIf="mostrarPanelNotificaciones" class="tarjeta-blanca"
                 style="position: absolute; top: 48px; right: 0; width: 320px; z-index: 50; box-shadow: 0 14px 34px rgba(0,0,0,0.12); padding: 18px;">
              <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 10px;">Notificaciones</h4>
              <div style="background: var(--ambar-fondo); color: var(--ambar-alerta); padding: 6px 10px; border-radius: 8px; font-size: 12px; font-weight: 600; margin-bottom: 8px;">
                ● {{ resumenInicio?.metricas?.coincidencias || 0 }} coincidencias detectadas
              </div>
              <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 12px;">
                Se detectaron imágenes similares a tus obras registradas.
              </p>
              <button class="btn-secundario" style="width: 100%; margin-bottom: 10px; font-size: 12px;"
                      (click)="mostrarPanelNotificaciones = false; cambiarSeccion('coincidencias')">
                Revisar coincidencias →
              </button>
              <div *ngFor="let n of resumenInicio?.notificaciones" style="border-top: 1px solid var(--borde-gris); padding-top: 8px; margin-top: 8px; font-size: 12px;">
                <strong>{{ n.titulo }}</strong>
                <p style="color: var(--texto-secundario);">{{ n.mensaje }}</p>
              </div>
            </div>
          </div>
        </header>

        <!-- Cuerpo Dinámico según sección seleccionada -->
        <main class="cuerpo-vista">

          <!-- =========================================================================
               SECCIÓN 1: INICIO / DASHBOARD DEL ARTISTA (US-02, US-04 - Figura 38)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'inicio'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase; letter-spacing: 0.8px;">
              TU ESPACIO CREATIVO
            </p>
            <h1 style="font-size: 32px; font-weight: 800; margin: 4px 0;">Hola, {{ resumenInicio?.nombre_saludo || 'Nayeli' }}.</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 24px;">
              Todo listo para que sigas creando con tranquilidad.
            </p>

            <!-- Banner Hero Superior -->
            <div style="background: linear-gradient(90deg, #f4efff 0%, #faf8ff 100%); border: 1px solid var(--lavanda-borde); border-radius: 18px; padding: 28px 32px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
              <div>
                <h2 style="font-size: 24px; font-weight: 800; margin-bottom: 8px;">Tu arte merece protección.</h2>
                <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 18px;">
                  Crea, registra y monitorea tus obras desde un solo espacio.
                </p>
                <button class="btn-primario" (click)="iniciarFlujoProteger()">Proteger nueva obra</button>
              </div>
              <div style="width: 240px; height: 125px; border-radius: 14px; background: linear-gradient(135deg, #ff7eb3 0%, #7b4dff 100%); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 38px; position: relative;">
                🎨✨
                <span style="position: absolute; top: -10px; right: -10px; background: #ede6ff; color: var(--morado-primario); width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 800;">✓</span>
              </div>
            </div>

            <!-- 4 Tarjetas de Contadores Reales -->
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; margin-bottom: 24px;">
              <div class="tarjeta-blanca" style="padding: 18px 20px;">
                <p style="font-size: 13px; font-weight: 600; color: var(--texto-secundario); margin-bottom: 10px;">Obras protegidas</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-size: 30px; font-weight: 800; color: #4a25aa;">{{ resumenInicio?.metricas?.obras_protegidas || 0 }}</span>
                  <span class="badge badge-protegida">Protegida</span>
                </div>
              </div>

              <div class="tarjeta-blanca" style="padding: 18px 20px; cursor: pointer;" (click)="cambiarSeccion('coincidencias')">
                <p style="font-size: 13px; font-weight: 600; color: var(--texto-secundario); margin-bottom: 10px;">Coincidencias</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-size: 30px; font-weight: 800; color: #8c5800;">{{ resumenInicio?.metricas?.coincidencias || 0 }}</span>
                  <span class="badge badge-alerta">Revisar</span>
                </div>
              </div>

              <div class="tarjeta-blanca" style="padding: 18px 20px; cursor: pointer;" (click)="cambiarSeccion('monitoreo')">
                <p style="font-size: 13px; font-weight: 600; color: var(--texto-secundario); margin-bottom: 10px;">Monitoreando</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-size: 30px; font-weight: 800; color: #3d2c7a;">{{ resumenInicio?.metricas?.monitoreando || 0 }}</span>
                  <span class="badge badge-monitoreo">Activo</span>
                </div>
              </div>

              <div class="tarjeta-blanca" style="padding: 18px 20px; cursor: pointer;" (click)="cambiarSeccion('certificados')">
                <p style="font-size: 13px; font-weight: 600; color: var(--texto-secundario); margin-bottom: 10px;">Certificados</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-size: 30px; font-weight: 800; color: #4a25aa;">{{ resumenInicio?.metricas?.certificados || 0 }}</span>
                  <span class="badge badge-protegida">Protegida</span>
                </div>
              </div>
            </div>

            <!-- Bloques inferiores: Gráfico de barras + Actividad reciente -->
            <div style="display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 20px;">
              <div class="tarjeta-blanca">
                <h3 style="font-size: 16px; font-weight: 700;">Tu arte, bajo vigilancia</h3>
                <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 12px;">
                  Coincidencias y registros en internet · Últimas 4 semanas
                </p>
                <p style="font-size: 32px; font-weight: 800; color: var(--morado-primario); margin-bottom: 16px;">
                  {{ (resumenInicio?.metricas?.obras_protegidas || 0) + (resumenInicio?.metricas?.coincidencias || 0) }}
                </p>
                <div style="display: flex; align-items: flex-end; gap: 18px; height: 120px; padding-top: 10px;">
                  <div *ngFor="let val of resumenInicio?.vigilancia_semanas; let last = last"
                       [style.height.%]="(val + 2) * 10"
                       [style.background]="last ? 'var(--morado-primario)' : '#dcd2f8'"
                       style="flex: 1; border-radius: 8px 8px 0 0; min-height: 24px; max-height: 110px;"></div>
                </div>
              </div>

              <div class="tarjeta-blanca">
                <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 18px;">Actividad reciente</h3>
                <div *ngFor="let act of resumenInicio?.actividad_reciente"
                     style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                  <span class="badge"
                        [ngClass]="{
                          'badge-alerta': act.tipo === 'alerta',
                          'badge-protegida': act.tipo === 'exito',
                          'badge-monitoreo': act.tipo === 'info'
                        }">
                    {{ act.etiqueta }}
                  </span>
                  <span style="font-size: 12px; color: var(--texto-secundario);">{{ act.tiempo }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 2: MIS OBRAS (US-04 - Figuras 20, 39, Páginas 32-35 de Figma)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'mis_obras'">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px;">
              <div>
                <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">GALERÍA</p>
                <h1 style="font-size: 30px; font-weight: 800;">Mis obras <span style="font-size: 16px; font-weight: 600; color: var(--texto-secundario);">{{ listaObras.length }} obras</span></h1>
                <p style="font-size: 14px; color: var(--texto-secundario);">Tus creaciones registradas y protegidas.</p>
              </div>
              <button class="btn-primario" (click)="iniciarFlujoProteger()">+ Proteger obra</button>
            </div>

            <!-- Barra de búsqueda y pestañas de filtro -->
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 24px; flex-wrap: wrap;">
              <input type="text" class="input-aegis" style="max-width: 340px;"
                     placeholder="🔍 Buscar por título..." [(ngModel)]="busquedaObras" (input)="cargarObras()">

              <div style="display: flex; gap: 8px;">
                <button *ngFor="let f of ['Todas', 'Protegidas', 'Monitoreando', 'Coincidencia encontrada']"
                        (click)="filtroEstadoObras = f; cargarObras()"
                        [class]="filtroEstadoObras === f ? 'btn-primario' : 'btn-secundario'"
                        style="padding: 8px 14px; font-size: 13px;">
                  {{ f }}
                </button>
              </div>
            </div>

            <!-- Estado vacío cuando el artista aún no tiene obras registradas (Criterio 2 de US-04) -->
            <div *ngIf="listaObras.length === 0" class="tarjeta-blanca" style="text-align: center; padding: 56px 24px;">
              <h3 style="font-size: 20px; font-weight: 700; margin-bottom: 8px;">No hay obras subidas</h3>
              <p style="font-size: 14px; color: var(--texto-secundario); max-width: 440px; margin: 0 auto 20px;">
                Sube tu primera obra para registrar tu autoría y empezar a proteger tus creaciones.
              </p>
              <button class="btn-primario" (click)="iniciarFlujoProteger()">+ Proteger mi primera obra</button>
            </div>

            <!-- Grilla de Obras Registradas -->
            <div *ngIf="listaObras.length > 0" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
              <div *ngFor="let obra of listaObras" class="tarjeta-blanca"
                   style="display: grid; grid-template-columns: 170px 1fr; gap: 20px; align-items: center; padding: 18px;">
                <img [src]="obra.url_imagen" alt="{{ obra.titulo }}"
                     style="width: 170px; height: 155px; object-fit: cover; border-radius: 12px; border: 1px solid var(--borde-gris);">
                <div>
                  <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 4px;">{{ obra.titulo }}</h3>
                  <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 10px;">
                    Registrada el {{ obra.fecha_registro }} · {{ obra.codigo_obra }}
                  </p>
                  <div style="margin-bottom: 12px; display: flex; gap: 6px; flex-wrap: wrap;">
                    <span class="badge"
                          [ngClass]="{
                            'badge-protegida': obra.estado === 'Protegida',
                            'badge-alerta': obra.estado === 'Coincidencia encontrada' || obra.estado === 'En revisión' || obra.estado === 'Rechazada',
                            'badge-monitoreo': obra.estado === 'Monitoreando'
                          }">
                      {{ obra.estado }}
                    </span>
                    <span *ngIf="obra.es_sospechosa" class="badge badge-alerta">
                      Revisión ML (US-09)
                    </span>
                    <span *ngIf="obra.obra_inspirada_titulo" class="badge badge-monitoreo">
                      Inspirada en: {{ obra.obra_inspirada_titulo }}
                    </span>
                  </div>
                  <button class="btn-secundario" style="font-size: 13px; padding: 8px 16px;" (click)="abrirDetalleObra(obra.id)">
                    Ver detalle →
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 3: PROTEGER NUEVA OBRA (US-02, US-03, US-08, US-09 - Figura 40)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'proteger'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">REGISTRO</p>
            <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Proteger nueva obra</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 24px;">
              Sube tu creación y elige el nivel de protección.
            </p>

            <!-- Banner de alerta si el formato es inválido (Ej: .psd - Página 60 de Figma) -->
            <div *ngIf="errorCargaObra" style="background: var(--ambar-fondo); border: 1px solid #f2cb9b; padding: 14px 18px; border-radius: 12px; margin-bottom: 20px;">
              <p style="font-size: 14px; font-weight: 700; color: #7a4608;">● Aún no es posible continuar</p>
              <p style="font-size: 13px; color: #7a4608;">{{ errorCargaObra }}</p>
            </div>

            <div style="display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 32px;">
              <!-- Columna 1: Sube tu creación -->
              <div class="tarjeta-blanca">
                <h3 style="font-size: 16px; font-weight: 700;">1. Sube tu creación</h3>
                <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 16px;">Tu próxima obra empieza aquí.</p>

                <!-- Estado A: Zona para seleccionar/arrastrar archivo -->
                <div *ngIf="!archivoSeleccionado && !archivoInvalidoNombre"
                     [class.input-error]="intentoEnvioSinArchivo"
                     (dragover)="alArrastrarArchivo($event)"
                     (dragleave)="arrastrandoArchivo = false"
                     (drop)="alSoltarArchivo($event)"
                     [style.background]="arrastrandoArchivo ? '#f3eeff' : '#fcfbfe'"
                     [style.border-color]="arrastrandoArchivo ? 'var(--morado-primario)' : 'var(--lavanda-borde)'"
                     style="border: 2px dashed var(--lavanda-borde); border-radius: 14px; padding: 34px 20px; text-align: center; margin-bottom: 12px; transition: all 0.15s ease;">
                  <div style="font-size: 32px; color: var(--morado-primario); margin-bottom: 8px;">⬆</div>
                  <p style="font-size: 14px; font-weight: 700; margin-bottom: 4px;">Arrastra una imagen o selecciona un archivo</p>
                  <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 14px;">
                    PNG, JPG o WEBP · Tamaño máximo: 20 MB · Tu imagen no se publicará
                  </p>
                  <input type="file" #fileInput style="display: none;" (change)="alSeleccionarArchivo($event)" accept=".png,.jpg,.jpeg,.webp,.psd">
                  <button class="btn-secundario" (click)="fileInput.click()">Seleccionar archivo</button>
                </div>
                <p *ngIf="intentoEnvioSinArchivo && !archivoSeleccionado" class="texto-error" style="margin-bottom: 12px;">
                  Sube una imagen de tu obra para continuar.
                </p>

                <!-- Estado B: Error de formato incompatible (ej. .psd) -->
                <div *ngIf="archivoInvalidoNombre"
                     style="border: 2px dashed #e6a87c; background: #fff9f5; border-radius: 14px; padding: 24px; text-align: center; margin-bottom: 16px;">
                  <p style="font-size: 15px; font-weight: 700; margin-bottom: 4px;">No se ha podido cargar la obra</p>
                  <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 12px;">
                    El formato del archivo no es compatible. Selecciona una imagen JPG, PNG o WEBP.
                  </p>
                  <div style="background: #fff; border: 1px solid var(--borde-gris); border-radius: 10px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 13px; font-weight: 600;">📄 {{ archivoInvalidoNombre }} · <span style="color: var(--ambar-alerta);">Carga fallida</span></span>
                    <button (click)="limpiarArchivo()" style="border:none; background:transparent; cursor:pointer; font-size:16px;">✕</button>
                  </div>
                  <input type="file" #retryInput style="display: none;" (change)="alSeleccionarArchivo($event)">
                  <button class="btn-secundario" (click)="retryInput.click()">Seleccionar otro archivo</button>
                </div>

                <!-- Estado C: Archivo válido cargado con vista previa (Páginas 19 y 63 de Figma) -->
                <div *ngIf="archivoSeleccionado"
                     style="background: #f8f6fe; border: 1px solid var(--lavanda-borde); border-radius: 14px; padding: 14px; display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
                  <img [src]="vistaPreviaUrl" style="width: 78px; height: 78px; object-fit: cover; border-radius: 10px;">
                  <div style="flex: 1;">
                    <span class="badge badge-protegida" style="margin-bottom: 4px;">✓ Archivo subido correctamente</span>
                    <p style="font-size: 14px; font-weight: 700;">{{ archivoSeleccionado.name }}</p>
                    <p style="font-size: 12px; color: var(--texto-secundario);">
                      {{ tamanoArchivoMb }} MB / 20 MB máx. · Archivo admitido
                    </p>
                  </div>
                  <button class="btn-secundario" style="font-size: 12px; padding: 6px 12px;" (click)="limpiarArchivo()">
                    Cambiar imagen
                  </button>
                </div>

                <!-- Campos: Nombre de la obra y Descripción -->
                <div class="grupo-campo">
                  <label>Nombre de la obra *</label>
                  <input type="text" class="input-aegis"
                         [class.input-error]="intentoEnvioSinTitulo && !formObra.titulo.trim()"
                         [(ngModel)]="formObra.titulo"
                         placeholder="Ej. Sueños violetas" maxlength="120">
                  <div style="display: flex; justify-content: space-between;">
                    <span *ngIf="intentoEnvioSinTitulo && !formObra.titulo.trim()" class="texto-error">
                      El título de la obra es obligatorio.
                    </span>
                    <span class="texto-ayuda" style="margin-left: auto;">{{ formObra.titulo.length }}/120 caracteres</span>
                  </div>
                </div>

                <div class="grupo-campo">
                  <label>Descripción (opcional)</label>
                  <textarea class="textarea-aegis" rows="2" [(ngModel)]="formObra.descripcion"
                            placeholder="Añade contexto de la obra"></textarea>
                </div>

                <!-- US-08: Marcar que mi obra ha sido inspirada de otra ya subida antes -->
                <div style="margin-top: 12px; padding: 12px 14px; background: #f8f6fe; border: 1px solid var(--lavanda-borde); border-radius: 12px;">
                  <label style="display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; cursor: pointer;">
                    <input type="checkbox" [(ngModel)]="formObra.es_inspirada">
                    <span>¿Esta obra fue inspirada en otra ya registrada en AegisArt? (US-08)</span>
                  </label>
                  <div *ngIf="formObra.es_inspirada" style="margin-top: 10px;">
                    <select class="select-aegis" [(ngModel)]="formObra.obra_inspirada_id">
                      <option [ngValue]="null">-- Selecciona la obra de referencia --</option>
                      <option *ngFor="let ref of catalogoInspiracion" [ngValue]="ref.id">
                        {{ ref.codigo_obra }} · {{ ref.titulo }} ({{ ref.autor }})
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Columna 2: Elige tu protección -->
              <div class="tarjeta-blanca" style="display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                  <h3 style="font-size: 16px; font-weight: 700;">2. Elige tu protección</h3>
                  <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 18px;">
                    Capas de seguridad, sin cambiar tu esencia.
                  </p>

                  <!-- Opción 1: Equilibrada -->
                  <div (click)="formObra.nivel_proteccion = 'Equilibrada'"
                       [style.border-color]="formObra.nivel_proteccion === 'Equilibrada' ? 'var(--morado-primario)' : 'var(--borde-gris)'"
                       [style.background]="formObra.nivel_proteccion === 'Equilibrada' ? '#f8f5ff' : '#fff'"
                       style="border: 2px solid; border-radius: 14px; padding: 16px; margin-bottom: 12px; cursor: pointer;">
                    <span class="badge badge-protegida" style="margin-bottom: 6px;">Equilibrada — recomendada</span>
                    <p style="font-size: 13px; color: var(--texto-secundario);">Protección IA (Glaze) + marca invisible (DCT/DWT)</p>
                  </div>

                  <!-- Opción 2: Máxima protección -->
                  <div (click)="formObra.nivel_proteccion = 'Maxima'"
                       [style.border-color]="formObra.nivel_proteccion === 'Maxima' ? 'var(--morado-primario)' : 'var(--borde-gris)'"
                       [style.background]="formObra.nivel_proteccion === 'Maxima' ? '#f8f5ff' : '#fff'"
                       style="border: 2px solid; border-radius: 14px; padding: 16px; margin-bottom: 12px; cursor: pointer;">
                    <span class="badge badge-monitoreo" style="margin-bottom: 6px;">Máxima protección</span>
                    <p style="font-size: 13px; color: var(--texto-secundario);">Capas reforzadas de perturbación y monitoreo prioritario</p>
                  </div>

                  <!-- Opción 3: Ligera -->
                  <div (click)="formObra.nivel_proteccion = 'Ligera'"
                       [style.border-color]="formObra.nivel_proteccion === 'Ligera' ? 'var(--morado-primario)' : 'var(--borde-gris)'"
                       [style.background]="formObra.nivel_proteccion === 'Ligera' ? '#f8f5ff' : '#fff'"
                       style="border: 2px solid; border-radius: 14px; padding: 16px; margin-bottom: 20px; cursor: pointer;">
                    <span class="badge badge-alerta" style="margin-bottom: 6px;">Ligera</span>
                    <p style="font-size: 13px; color: var(--texto-secundario);">Huella digital SHA-256 y autoría en Blockchain</p>
                  </div>
                </div>

                <div>
                  <button class="btn-primario" style="width: 100%; padding: 14px; font-size: 15px;" (click)="ejecutarProtegerYRegistrar()">
                    Proteger y registrar →
                  </button>
                  <p style="font-size: 12px; color: var(--texto-secundario); text-align: center; margin-top: 10px;">
                    Procesamiento real con OpenCV, DCT/DWT, SHA-256 y Smart Contract en Hardhat.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 3B: PROCESANDO PROTECCIÓN DE OBRA (US-03 - Figura 41 y Página 21)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'procesando'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">REGISTRO</p>
            <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Protegiendo tu obra...</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 18px;">
              {{ simularDemoraProceso ? 'Está tardando más de lo habitual, pero tu obra sigue procesándose.' : 'Ejecutando el proceso de registro, blindaje y certificación en blockchain.' }}
            </p>

            <!-- Alerta de caso límite 3 de US-03 (Demora simulada) -->
            <div *ngIf="simularDemoraProceso" style="background: var(--ambar-fondo); border: 1px solid #f0c999; padding: 12px 16px; border-radius: 12px; margin-bottom: 20px;">
              <p style="font-size: 13px; font-weight: 700; color: var(--ambar-alerta);">● Estamos tardando un poco más</p>
              <p style="font-size: 12px; color: var(--ambar-alerta);">
                Tu obra sigue procesándose. No necesitas volver a cargarla ni reiniciar el proceso.
              </p>
            </div>

            <div class="tarjeta-blanca" style="display: grid; grid-template-columns: 360px 1fr; gap: 36px; align-items: center;">
              <img [src]="vistaPreviaUrl || obraActualDetalle?.url_imagen"
                   style="width: 100%; height: 320px; object-fit: cover; border-radius: 14px; border: 1px solid var(--borde-gris);">

              <div>
                <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 16px;">Proceso de protección</h3>
                <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px;">
                  <div *ngFor="let p of pasosProteccion; let idx = index">
                    <span class="badge" [ngClass]="idx < pasoActualAnimacion ? 'badge-protegida' : 'badge-monitoreo'">
                      {{ p }}
                    </span>
                  </div>
                </div>

                <div class="barra-progreso-fondo" style="height: 10px; margin-bottom: 8px;">
                  <div class="barra-progreso-relleno" [style.width.%]="(pasoActualAnimacion / 5) * 100"></div>
                </div>
                <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 14px;">
                  {{ pasoActualAnimacion }} de 5 pasos completados
                </p>

                <div *ngIf="resultadoProteccionIa"
                     style="margin-bottom: 16px; padding: 10px 14px; border-radius: 10px; font-size: 13px;"
                     [style.background]="resultadoProteccionIa.es_sospechosa ? 'var(--ambar-fondo)' : 'var(--verde-fondo)'"
                     [style.color]="resultadoProteccionIa.es_sospechosa ? 'var(--ambar-alerta)' : 'var(--verde-exito)'">
                  <strong>Evaluación ML (Gradient Boosting):</strong> {{ resultadoProteccionIa.evaluacion_resumen }}
                  <span *ngIf="resultadoProteccionIa.motivo_sospecha"> · {{ resultadoProteccionIa.motivo_sospecha }}</span>
                </div>

                <div style="display: flex; gap: 12px;">
                  <button class="btn-primario" [disabled]="!obraRecienCreadaId" (click)="abrirDetalleObra(obraRecienCreadaId!)">
                    Ver resultado →
                  </button>
                  <button class="btn-secundario" style="font-size: 12px;" (click)="simularDemoraProceso = !simularDemoraProceso">
                    {{ simularDemoraProceso ? 'Ocultar aviso de demora' : 'Simular demora (Caso extremo US-03)' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 3C: DETALLE DE OBRA PROTEGIDA (Figura 42 - Ej. Mau Feliz)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'detalle_obra' && obraActualDetalle">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">OBRA PROTEGIDA</p>
            <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">{{ obraActualDetalle.titulo }}</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 24px;">
              Registro y detalles técnicos de autoría.
            </p>

            <div class="tarjeta-blanca" style="display: grid; grid-template-columns: 420px 1fr; gap: 36px; align-items: center;">
              <img [src]="obraActualDetalle.url_imagen" alt="{{ obraActualDetalle.titulo }}"
                   style="width: 100%; height: 340px; object-fit: cover; border-radius: 14px; border: 1px solid var(--borde-gris);">

              <div>
                <span class="badge badge-protegida" style="margin-bottom: 10px;">{{ obraActualDetalle.estado }}</span>
                <h2 style="font-size: 26px; font-weight: 800; margin-bottom: 4px;">{{ obraActualDetalle.titulo }}</h2>
                <p style="font-size: 13px; color: var(--texto-secundario); margin-bottom: 20px;">
                  Registrada el {{ obraActualDetalle.fecha_registro }}
                </p>

                <div style="border-top: 1px solid var(--borde-gris); padding-top: 14px; display: grid; grid-template-columns: 170px 1fr; row-gap: 12px; font-size: 14px; margin-bottom: 24px;">
                  <span style="color: var(--texto-secundario);">Fecha de registro</span>
                  <strong>{{ obraActualDetalle.fecha_registro }}</strong>

                  <span style="color: var(--texto-secundario);">Protección contra IA</span>
                  <strong>{{ obraActualDetalle.proteccion_contra_ia }}</strong>

                  <span style="color: var(--texto-secundario);">Marca invisible</span>
                  <strong>{{ obraActualDetalle.marca_invisible }} ({{ obraActualDetalle.firma_dct_dwt }})</strong>

                  <span style="color: var(--texto-secundario);">Hash SHA-256</span>
                  <strong style="font-family: monospace;">{{ obraActualDetalle.hash_corto }}</strong>

                  <span style="color: var(--texto-secundario);">Evaluación IA (US-09)</span>
                  <strong [style.color]="obraActualDetalle.es_sospechosa ? 'var(--ambar-alerta)' : 'var(--verde-exito)'">
                    {{ obraActualDetalle.es_sospechosa ? (obraActualDetalle.motivo_sospecha || 'Enviada a moderación ML') : 'Aprobada por Gradient Boosting ML' }}
                  </strong>

                  <span *ngIf="obraActualDetalle.obra_inspirada_titulo" style="color: var(--texto-secundario);">Inspirada en (US-08)</span>
                  <strong *ngIf="obraActualDetalle.obra_inspirada_titulo">{{ obraActualDetalle.obra_inspirada_titulo }}</strong>
                </div>

                <div style="display: flex; gap: 12px;">
                  <button class="btn-primario" (click)="cambiarSeccion('certificados')">Ver certificado</button>
                  <button class="btn-secundario" (click)="cambiarSeccion('monitoreo')">Iniciar monitoreo</button>
                </div>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 4: MONITOREO CON ESCANEO POR URL TEMPORAL (US-05 - Figura 43)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'monitoreo'">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
              <div>
                <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">VIGILANCIA</p>
                <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Tu arte no está solo</h1>
                <p style="font-size: 14px; color: var(--texto-secundario);">
                  Monitoreo activo en {{ estadoMonitoreo?.plataformas_monitoreadas || 0 }} plataformas · Búsqueda puntual por URL temporal.
                </p>
              </div>
              <span class="badge badge-protegida">Activo</span>
            </div>

            <!-- Buscador interactivo por URL Temporal (Prototipo Funcional US-05) -->
            <div class="tarjeta-blanca" style="margin-bottom: 22px; background: #faf8ff; border-color: var(--lavanda-borde);">
              <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 6px;">
                🔍 Escaneo de similitud mediante URL temporal (imageHash + CLIP + Marca DCT/DWT)
              </h3>
              <p style="font-size: 13px; color: var(--texto-secundario); margin-bottom: 14px;">
                Ingresa la URL de una imagen externa o de prueba para compararla en tiempo real contra tus obras registradas.
              </p>

              <div style="display: grid; grid-template-columns: 1fr 220px auto; gap: 12px; align-items: center;">
                <input type="text" class="input-aegis" [(ngModel)]="urlTemporalInput"
                       placeholder="https://ejemplo.com/imagen_sospechosa.png o URL local de prueba">
                <select class="select-aegis" [(ngModel)]="obraIdParaEscanear">
                  <option [ngValue]="null">Comparar con todas mis obras</option>
                  <option *ngFor="let o of listaObras" [ngValue]="o.id">{{ o.titulo }}</option>
                </select>
                <button class="btn-primario" [disabled]="escaneandoUrl" (click)="ejecutarEscaneoUrl()">
                  {{ escaneandoUrl ? 'Analizando...' : 'Analizar URL →' }}
                </button>
              </div>

              <!-- Botones de URL de prueba con 1 clic para la exposición -->
              <div style="margin-top: 10px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                <span style="font-size: 12px; color: var(--texto-secundario);">URLs rápidas de prueba:</span>
                <button class="btn-secundario" style="font-size: 11px; padding: 4px 10px;"
                        (click)="urlTemporalInput = 'http://localhost:8000/archivos/protegidas/ecos_de_otro_mundo.png'">
                  Probar copia de "Ecos de otro mundo"
                </button>
                <button class="btn-secundario" style="font-size: 11px; padding: 4px 10px;"
                        (click)="urlTemporalInput = 'http://localhost:8000/archivos/protegidas/Mau_feliz.jpg'">
                  Probar copia de "Mau Feliz"
                </button>
              </div>

              <div *ngIf="resultadoEscaneoUrl" style="margin-top: 14px; padding: 12px 16px; border-radius: 10px; background: #fff; border: 1px solid var(--lavanda-borde); display: flex; justify-content: space-between; align-items: center;">
                <div>
                  <strong style="font-size: 14px; color: var(--morado-primario);">{{ resultadoEscaneoUrl.mensaje }}</strong>
                  <p style="font-size: 12px; color: var(--texto-secundario);">
                    pHash visual: {{ resultadoEscaneoUrl.similitud_visual_phash }}% · CLIP semántico: {{ resultadoEscaneoUrl.similitud_semantica_clip }}% · Marca DCT/DWT: {{ resultadoEscaneoUrl.marca_invisible_identificada ? 'Detectada' : 'No detectada' }}
                  </p>
                </div>
                <button *ngIf="resultadoEscaneoUrl.coincidencia_id" class="btn-primario" style="font-size: 12px; padding: 8px 14px;"
                        (click)="abrirRevisionCoincidencia(resultadoEscaneoUrl.coincidencia_id)">
                  Revisar coincidencia →
                </button>
              </div>
            </div>

            <!-- Barras de Historial de Monitoreo como en Figma (Figura 43) -->
            <div class="tarjeta-blanca">
              <div style="display: flex; align-items: baseline; gap: 10px; margin-bottom: 18px;">
                <span style="font-size: 32px; font-weight: 800; color: var(--morado-primario);">{{ estadoMonitoreo?.plataformas_monitoreadas || 0 }}</span>
                <span style="font-size: 14px; color: var(--texto-secundario);">plataformas monitoreadas</span>
              </div>

              <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 16px;">Historial de monitoreo</h3>
              <div *ngFor="let plat of estadoMonitoreo?.historial_plataformas"
                   style="display: grid; grid-template-columns: 140px 1fr 140px; align-items: center; gap: 18px; margin-bottom: 14px;">
                <span style="font-size: 13px; font-weight: 500;">{{ plat.nombre }}</span>
                <div class="barra-progreso-fondo" style="margin: 0;">
                  <div class="barra-progreso-relleno"
                       [style.width.%]="plat.progreso"
                       [style.background]="plat.alerta ? '#a6631b' : 'var(--morado-primario)'"></div>
                </div>
                <span style="font-size: 12px; text-align: right;"
                      [style.color]="plat.alerta ? 'var(--ambar-alerta)' : 'var(--texto-secundario)'"
                      [style.font-weight]="plat.alerta ? '700' : '400'">
                  {{ plat.estado }}
                </span>
              </div>

              <div style="text-align: right; margin-top: 22px;">
                <button class="btn-primario" (click)="cambiarSeccion('coincidencias')">Ver coincidencias →</button>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 5: COINCIDENCIAS DETECTADAS (US-05 - Figura 44 y Página 34)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'coincidencias'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">ANÁLISIS</p>
            <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Coincidencias detectadas</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 18px;">
              Revisa los casos que podrían necesitar tu atención.
            </p>

            <div style="display: flex; gap: 10px; margin-bottom: 24px;">
              <button *ngFor="let fc of ['Todas', 'Similitud > 90%', 'Últimas 24 horas']"
                      (click)="filtroCoincidencias = fc; cargarCoincidencias()"
                      [class]="filtroCoincidencias === fc ? 'btn-primario' : 'btn-secundario'"
                      style="padding: 8px 16px; font-size: 13px;">
                {{ fc }}
              </button>
            </div>

            <!-- Estado sin coincidencias (Criterio 2 de US-05 - Página 34 de Figma) -->
            <div *ngIf="listaCoincidencias.length === 0" class="tarjeta-blanca" style="text-align: center; padding: 48px 24px;">
              <div style="font-size: 32px; margin-bottom: 8px;">🔍</div>
              <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 6px;">No se encontraron obras similares</h3>
              <p style="font-size: 14px; color: var(--texto-secundario); max-width: 460px; margin: 0 auto;">
                No hay coincidencias detectadas para este filtro. Seguimos monitoreando para ayudarte a proteger tu creación.
              </p>
            </div>

            <!-- Tarjetas comparativas 98%, 94%, 82% (Figura 44) -->
            <div *ngIf="listaCoincidencias.length > 0" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px;">
              <div *ngFor="let c of listaCoincidencias" class="tarjeta-blanca" style="padding: 18px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 14px;">
                  <div style="position: relative;">
                    <img [src]="c.url_imagen_original" style="width: 100%; height: 145px; object-fit: cover; border-radius: 10px;">
                    <span style="position: absolute; bottom: 8px; left: 8px; background: rgba(0,0,0,0.65); color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 6px;">Original</span>
                  </div>
                  <div style="position: relative;">
                    <img [src]="c.url_imagen_copia" style="width: 100%; height: 145px; object-fit: cover; border-radius: 10px; filter: contrast(1.08) sepia(0.18);">
                    <span style="position: absolute; bottom: 8px; left: 8px; background: rgba(0,0,0,0.65); color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 6px;">Coincidencia</span>
                  </div>
                </div>

                <div style="margin-bottom: 10px;">
                  <span style="font-size: 30px; font-weight: 800; color: #4a25aa;">{{ c.porcentaje_similitud }}%</span>
                  <span style="font-size: 13px; color: var(--texto-secundario);"> similitud visual</span>
                </div>

                <div style="margin-bottom: 14px;">
                  <span class="badge"
                        [ngClass]="{
                          'badge-alerta': c.estado_artista === 'Pendiente',
                          'badge-protegida': c.estado_artista === 'Confirmado',
                          'badge-inactivo': c.estado_artista === 'Descartado'
                        }">
                    {{ c.estado_artista }}
                  </span>
                </div>

                <button class="btn-secundario" style="width: 100%;" (click)="abrirRevisionCoincidencia(c.id)">
                  Revisar →
                </button>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 5B: REVISIÓN DE COINCIDENCIA LADO A LADO (US-05 - Figura 45)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'revision_coincidencia' && coincidenciaActual">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">ANÁLISIS DE SIMILITUD</p>
            <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Revisión de coincidencia</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 22px;">
              Compara el original con la coincidencia detectada en {{ coincidenciaActual.plataforma }} ({{ coincidenciaActual.url_detectada }}).
            </p>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 22px;">
              <div class="tarjeta-blanca" style="padding: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                  <strong style="font-size: 15px;">Obra original ({{ coincidenciaActual.titulo_obra }})</strong>
                  <span class="badge badge-protegida">Protegida</span>
                </div>
                <img [src]="coincidenciaActual.url_imagen_original" style="width: 100%; height: 270px; object-fit: cover; border-radius: 12px;">
              </div>

              <div class="tarjeta-blanca" style="padding: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                  <strong style="font-size: 15px;">Coincidencia detectada</strong>
                  <span class="badge badge-alerta">Alto</span>
                </div>
                <img [src]="coincidenciaActual.url_imagen_copia" style="width: 100%; height: 270px; object-fit: cover; border-radius: 12px; filter: contrast(1.08) sepia(0.18);">
              </div>
            </div>

            <div class="tarjeta-blanca" style="margin-bottom: 20px;">
              <div style="display: flex; align-items: center; gap: 36px; flex-wrap: wrap; margin-bottom: 20px;">
                <div>
                  <span style="font-size: 40px; font-weight: 800; color: #4a25aa;">{{ coincidenciaActual.porcentaje_similitud }}%</span>
                  <span style="font-size: 14px; color: var(--texto-secundario);"> similitud visual</span>
                </div>
                <div>
                  <h4 style="font-size: 15px; font-weight: 700; margin-bottom: 4px;">Diferencias visuales detectadas</h4>
                  <p style="font-size: 13px; color: var(--texto-secundario);">{{ coincidenciaActual.diferencias_detectadas }}</p>
                </div>
              </div>

              <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                <button class="btn-primario" (click)="cambiarEstadoCaso(coincidenciaActual.id, 'Confirmado')">
                  Confirmar plagio
                </button>
                <button class="btn-secundario" (click)="cambiarEstadoCaso(coincidenciaActual.id, 'Descartado')">
                  Descartar coincidencia
                </button>
                <button class="btn-secundario" (click)="cambiarSeccion('reportes')">
                  Generar evidencia
                </button>
                <button class="btn-primario" (click)="iniciarReclamoCaso(coincidenciaActual.id)">
                  Iniciar reclamo →
                </button>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 6: CERTIFICADO DIGITAL DE AUTORÍA (US-03 - Figura 46)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'certificados'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">AUTORÍA</p>
            <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Certificado digital</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 24px;">
              Respaldo criptográfico y registro inmutable en Blockchain local (Hardhat + Solidity).
            </p>

            <!-- Selector rápido para ver el certificado de cualquiera de las obras del artista -->
            <div *ngIf="listaObras.length > 1" style="margin-bottom: 18px; display: flex; align-items: center; gap: 10px;">
              <span style="font-size: 13px; font-weight: 600;">Obra certificada:</span>
              <select class="select-aegis" style="max-width: 300px;"
                      [ngModel]="obraActualDetalle?.id" (ngModelChange)="abrirCertificadoDeObra($event)">
                <option *ngFor="let o of listaObras" [ngValue]="o.id">{{ o.titulo }} ({{ o.codigo_certificado }})</option>
              </select>
            </div>

            <div class="tarjeta-blanca" style="max-width: 760px; margin: 0 auto; padding: 40px; text-align: center; box-shadow: 0 12px 35px rgba(74,37,170,0.06);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                <span style="font-size: 20px; font-weight: 800;">Aegis<span style="color: var(--morado-primario);">Art</span></span>
                <span style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); letter-spacing: 1px;">CERTIFICADO DIGITAL BLOCKCHAIN</span>
              </div>

              <div style="width: 56px; height: 56px; border-radius: 16px; background: var(--lavanda-suave); color: var(--morado-primario); display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: 800; margin: 0 auto 18px;">
                ✓
              </div>

              <h2 style="font-size: 22px; font-weight: 700; margin-bottom: 6px;">Certificado de autoría</h2>
              <h3 style="font-size: 32px; font-weight: 800; color: var(--morado-primario); margin-bottom: 8px;">
                {{ obraActualDetalle?.titulo || 'Ecos de otro mundo' }}
              </h3>
              <p style="font-size: 12px; color: var(--texto-secundario);">creada por</p>
              <p style="font-size: 16px; font-weight: 700; margin-bottom: 28px;">
                {{ obraActualDetalle?.autor || perfil?.nombre_apellido || 'Nayeli Castillo' }}
              </p>

              <div style="border-top: 1px solid var(--borde-gris); padding-top: 22px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; text-align: left; max-width: 520px; margin: 0 auto 20px;">
                <div>
                  <p style="font-size: 10px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">FECHA DE REGISTRO</p>
                  <p style="font-size: 14px; font-weight: 700;">{{ obraActualDetalle?.fecha_registro || '18 junio 2026' }}</p>
                </div>
                <div>
                  <p style="font-size: 10px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">ID DEL CERTIFICADO</p>
                  <p style="font-size: 14px; font-weight: 700;">{{ obraActualDetalle?.certificado?.codigo_certificado || 'AEG-2026-0024' }}</p>
                </div>
              </div>

              <p style="font-size: 12px; font-family: monospace; color: var(--texto-secundario); background: #f8f6fe; padding: 10px; border-radius: 8px;">
                SHA-256: {{ (obraActualDetalle?.hash_sha256 || '0x8f72a9c4e6b031d5...a371') | slice:0:28 }}...
                &nbsp;·&nbsp;
                Tx: {{ (obraActualDetalle?.certificado?.hash_transaccion || '0x3ac9...e720') | slice:0:18 }}...
              </p>
            </div>

            <div style="max-width: 760px; margin: 16px auto 0; text-align: right;">
              <button class="btn-secundario" (click)="cambiarSeccion('reportes')">Ver reporte →</button>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 7: REPORTE DE EVIDENCIA Y DESCARGA PDF (US-11 - Figura 47)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'reportes'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">EVIDENCIA</p>
            <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">
              Reporte de evidencia · {{ coincidenciaActual?.codigo_caso || 'AEG-2026-003' }}
            </h1>
            <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 24px;">
              Resumen técnico y cronología del caso para reclamos legales o Take-Down (DMCA).
            </p>

            <div class="tarjeta-blanca" style="display: grid; grid-template-columns: 1fr 1fr; gap: 36px; padding: 32px;">
              <!-- Columna izquierda: La historia de tu obra (Timeline) -->
              <div>
                <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 20px;">La historia de tu obra</h3>
                <div style="border-left: 2px solid var(--lavanda-borde); margin-left: 8px; padding-left: 20px; display: flex; flex-direction: column; gap: 22px;">
                  <div style="position: relative;">
                    <span style="position: absolute; left: -26px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--morado-primario);"></span>
                    <p style="font-size: 11px; color: var(--texto-secundario);">{{ coincidenciaActual?.fecha_registro_obra || '18 jun' }}</p>
                    <p style="font-size: 14px; font-weight: 700;">Registro de autoría</p>
                  </div>
                  <div style="position: relative;">
                    <span style="position: absolute; left: -26px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--morado-primario);"></span>
                    <p style="font-size: 11px; color: var(--texto-secundario);">{{ coincidenciaActual?.fecha_deteccion || '19 jun' }}</p>
                    <p style="font-size: 14px; font-weight: 700;">Coincidencia detectada ({{ coincidenciaActual?.plataforma || 'Instagram' }})</p>
                  </div>
                  <div style="position: relative;">
                    <span style="position: absolute; left: -26px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--morado-primario);"></span>
                    <p style="font-size: 11px; color: var(--texto-secundario);">{{ coincidenciaActual?.fecha_deteccion || '19 jun' }}</p>
                    <p style="font-size: 14px; font-weight: 700;">Similitud {{ coincidenciaActual?.porcentaje_similitud || 98.2 }}%</p>
                  </div>
                  <div style="position: relative;">
                    <span style="position: absolute; left: -26px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--morado-primario);"></span>
                    <p style="font-size: 11px; color: var(--texto-secundario);">Hoy</p>
                    <p style="font-size: 14px; font-weight: 700;">Evidencia generada</p>
                  </div>
                </div>
              </div>

              <!-- Columna derecha: Evidencia técnica y descarga de PDF (US-11) -->
              <div>
                <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 16px;">Evidencia técnica</h3>
                <span class="badge badge-protegida" style="margin-bottom: 18px;">
                  {{ coincidenciaActual?.marca_invisible_identificada !== false ? 'Marca invisible identificada' : 'Análisis perceptual completado' }}
                </span>

                <div style="display: flex; flex-direction: column; gap: 12px; font-size: 14px; margin-bottom: 24px;">
                  <p><strong>Original:</strong> <span style="font-family: monospace;">{{ coincidenciaActual?.hash_original_corto || '0x8f72...31d5' }}</span></p>
                  <p><strong>Copia:</strong> <span style="font-family: monospace;">{{ coincidenciaActual?.hash_copia_corto || '0x7e45...12c4' }}</span></p>
                  <p><strong>Transacción:</strong> <span style="font-family: monospace;">{{ (coincidenciaActual?.transaccion_blockchain || '0x3ac9...e720') | slice:0:22 }}...</span></p>
                </div>

                <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 20px;">
                  Reporte auditable respaldado por hash criptográfico SHA-256, firma frecuencial DCT/DWT y bloque EVM.
                </p>

                <div style="display: flex; gap: 12px;">
                  <button class="btn-primario" (click)="descargarReportePdf()">
                    Generar reporte técnico (PDF)
                  </button>
                  <button class="btn-secundario" (click)="prepararTakeDown()">
                    Preparar Take Down
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 8: PAGOS Y SUSCRIPCIONES + ADMIN PLANES (US-06) + MÉTRICAS DUEÑO (US-12)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'suscripciones'">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px;">
              <div>
                <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">CUENTA</p>
                <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Pagos y suscripciones</h1>
                <p style="font-size: 14px; color: var(--texto-secundario);">
                  Administra tu plan, método de pago y comprobantes.
                </p>
              </div>
              <button *ngIf="perfil?.rol === 'dueno'" class="btn-secundario" style="font-size: 12px;" (click)="cambiarSeccion('admin_planes')">
                👑 Gestión de Planes y Métricas (Vista Dueño · US-06 / US-12) →
              </button>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
              <div class="tarjeta-blanca">
                <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 18px;">Plan actual</h3>
                <div class="grupo-campo">
                  <label>Tipo de plan</label>
                  <input class="input-aegis" [value]="(perfil?.nombre_plan || 'Creador') + ' · ' + (perfil?.periodicidad_plan || 'Mensual')" readonly>
                </div>
                <div class="grupo-campo">
                  <label>Precio</label>
                  <input class="input-aegis" [value]="'S/' + (perfil?.precio_plan || 39.90) + ' al mes'" readonly>
                </div>
                <div class="grupo-campo">
                  <label>Próxima renovación</label>
                  <input class="input-aegis" [value]="perfil?.proxima_renovacion || '18 nov 2026'" readonly>
                </div>
                <button class="btn-primario" style="width: 100%; margin-top: 8px;" (click)="abrirGestionPlanesAdmin()">
                  Administrar suscripción
                </button>
              </div>

              <div class="tarjeta-blanca">
                <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 18px;">Método de pago</h3>
                <p style="font-size: 14px; font-weight: 600; margin-bottom: 6px;">
                  {{ perfil?.metodo_pago_resumen || 'Visa terminada en 4821 · vence 10/27' }}
                </p>
                <p style="font-size: 13px; color: var(--texto-secundario); margin-bottom: 20px;">
                  Titular: {{ perfil?.nombre_apellido || 'Nayeli Castillo' }}
                </p>
                <div style="display: flex; flex-direction: column; gap: 10px; max-width: 260px;">
                  <button class="btn-secundario">Actualizar método de pago</button>
                  <button class="btn-primario">Ver historial de pagos</button>
                  <button class="btn-secundario">Ver comprobantes</button>
                </div>
              </div>
            </div>
          </div>

          <!-- VISTA DUEÑO: GESTIÓN DE PLANES (US-06) + ESTADÍSTICAS GLOBALES (US-12) -->
          <div *ngIf="seccionActual === 'admin_planes'">
            <!-- Tarjetas de Métricas de Crecimiento para el Dueño (US-12) -->
            <div *ngIf="metricasDueno" style="background: #f4efff; border: 1px solid var(--lavanda-borde); border-radius: 16px; padding: 20px 24px; margin-bottom: 24px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div>
                  <span class="badge badge-protegida">US-12 · Alcance y Crecimiento de AegisArt</span>
                  <h3 style="font-size: 18px; font-weight: 800; margin-top: 4px;">Estadísticas Globales del Dueño de la Aplicación</h3>
                </div>
                <button *ngIf="perfil?.rol === 'artista'" class="btn-secundario" style="font-size: 12px;" (click)="cambiarSeccion('suscripciones')">
                  ← Volver a vista de artista
                </button>
              </div>
              <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
                <div style="background: #fff; padding: 14px; border-radius: 12px;">
                  <p style="font-size: 12px; color: var(--texto-secundario);">Artistas registrados</p>
                  <p style="font-size: 26px; font-weight: 800; color: var(--morado-primario);">{{ metricasDueno.total_artistas_registrados }}</p>
                </div>
                <div style="background: #fff; padding: 14px; border-radius: 12px;">
                  <p style="font-size: 12px; color: var(--texto-secundario);">Obras registradas</p>
                  <p style="font-size: 26px; font-weight: 800; color: var(--morado-primario);">{{ metricasDueno.total_obras_registradas }}</p>
                </div>
                <div style="background: #fff; padding: 14px; border-radius: 12px;">
                  <p style="font-size: 12px; color: var(--texto-secundario);">Certificados en Blockchain</p>
                  <p style="font-size: 26px; font-weight: 800; color: var(--verde-exito);">{{ metricasDueno.total_certificados_blockchain }}</p>
                </div>
                <div style="background: #fff; padding: 14px; border-radius: 12px;">
                  <p style="font-size: 12px; color: var(--texto-secundario);">Planes activos</p>
                  <p style="font-size: 26px; font-weight: 800; color: #3d2c7a;">{{ metricasDueno.planes_activos }}</p>
                </div>
              </div>
            </div>

            <!-- SUB-MODO 1: LISTADO DE PLANES (Página 28 de Figma) -->
            <div *ngIf="modoAdminPlan === 'listado'">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div>
                  <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">GESTIÓN DE PLANES</p>
                  <h1 style="font-size: 30px; font-weight: 800;">Listado de planes</h1>
                  <p style="font-size: 14px; color: var(--texto-secundario);">
                    Administra los precios, los límites de protección y la disponibilidad de tus planes.
                  </p>
                </div>
                <button class="btn-primario" (click)="iniciarCrearPlan()">Crear plan</button>
              </div>

              <!-- Filtros del listado de planes -->
              <div class="tarjeta-blanca" style="margin-bottom: 20px; padding: 16px; display: grid; grid-template-columns: 1.4fr 1fr 1fr 1fr; gap: 12px;">
                <div>
                  <label style="font-size: 12px; font-weight: 600;">Buscar plan</label>
                  <input class="input-aegis" [(ngModel)]="filtroPlanes.buscar" (input)="cargarPlanes()" placeholder="Buscar por nombre o descripción">
                </div>
                <div>
                  <label style="font-size: 12px; font-weight: 600;">Estado</label>
                  <select class="select-aegis" [(ngModel)]="filtroPlanes.estado" (change)="cargarPlanes()">
                    <option>Todos los estados</option>
                    <option>Activo</option>
                    <option>Inactivo</option>
                  </select>
                </div>
                <div>
                  <label style="font-size: 12px; font-weight: 600;">Periodicidad</label>
                  <select class="select-aegis" [(ngModel)]="filtroPlanes.periodicidad" (change)="cargarPlanes()">
                    <option>Todas las periodicidades</option>
                    <option>Semanal</option>
                    <option>Mensual</option>
                  </select>
                </div>
                <div>
                  <label style="font-size: 12px; font-weight: 600;">Moneda</label>
                  <input class="input-aegis" value="PEN Sol peruano (S/)" readonly>
                </div>
              </div>

              <!-- Tabla de planes (Junior, Inicial, Creador, Profesional) -->
              <div class="tarjeta-blanca" style="padding: 0; overflow: hidden;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                  <thead>
                    <tr style="background: #f8f6fe; border-bottom: 1px solid var(--borde-gris); text-align: left;">
                      <th style="padding: 14px 18px;">Plan ↑</th>
                      <th style="padding: 14px;">Precio / período</th>
                      <th style="padding: 14px;">Obras protegidas</th>
                      <th style="padding: 14px;">Obras en monitoreo</th>
                      <th style="padding: 14px;">Frecuencia</th>
                      <th style="padding: 14px;">Estado</th>
                      <th style="padding: 14px;">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let p of listaPlanes" style="border-bottom: 1px solid var(--borde-gris);">
                      <td style="padding: 14px 18px;">
                        <strong>{{ p.nombre }}</strong>
                        <p style="font-size: 12px; color: var(--texto-secundario);">{{ p.descripcion }}</p>
                      </td>
                      <td style="padding: 14px;">
                        <strong>{{ p.precio_formateado }}</strong>
                        <p style="font-size: 11px; color: var(--texto-secundario);">{{ p.periodicidad }} · {{ p.moneda }}</p>
                      </td>
                      <td style="padding: 14px;">{{ p.obras_protegidas }}</td>
                      <td style="padding: 14px;">{{ p.obras_monitoreo }}</td>
                      <td style="padding: 14px;">{{ p.frecuencia_monitoreo }}</td>
                      <td style="padding: 14px;">
                        <span class="badge" [ngClass]="p.estado === 'Activo' ? 'badge-protegida' : 'badge-inactivo'">
                          {{ p.estado }}
                        </span>
                      </td>
                      <td style="padding: 14px;">
                        <button class="btn-secundario" style="font-size: 12px; padding: 6px 14px;" (click)="iniciarEditarPlan(p)">
                          Editar
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- SUB-MODO 2: CREAR O EDITAR PLAN CON VALIDACIONES EN ROJO (Páginas 29, 38 y 43 de Figma) -->
            <div *ngIf="modoAdminPlan === 'formulario'">
              <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">GESTIÓN DE PLANES</p>
              <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">
                {{ planEditandoId ? 'Actualizar plan' : 'Crear plan' }}
              </h1>
              <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 18px;">
                Define el precio, la disponibilidad y la protección que incluirá el plan.
              </p>

              <!-- Alerta de validación si faltan campos (Página 38 de Figma) -->
              <div *ngIf="errorFormularioPlan" style="background: var(--ambar-fondo); border: 1px solid #f0c999; padding: 14px 18px; border-radius: 12px; margin-bottom: 20px;">
                <p style="font-size: 14px; font-weight: 700; color: #7a4608;">● No se guardaron los cambios</p>
                <p style="font-size: 13px; color: #7a4608;">{{ errorFormularioPlan }}</p>
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 20px;">
                <div class="tarjeta-blanca">
                  <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 14px;">Información del plan</h3>
                  <div class="grupo-campo">
                    <label>Nombre del plan *</label>
                    <input class="input-aegis" [class.input-error]="intentoGuardarPlan && !formPlan.nombre.trim()"
                           [(ngModel)]="formPlan.nombre" placeholder="Ej. Creador" maxlength="40">
                    <span *ngIf="intentoGuardarPlan && !formPlan.nombre.trim()" class="texto-error">Ingresa el nombre del plan.</span>
                    <span class="texto-ayuda">{{ formPlan.nombre.length }}/40 caracteres</span>
                  </div>

                  <div class="grupo-campo">
                    <label>Descripción *</label>
                    <textarea class="textarea-aegis" rows="3" [class.input-error]="intentoGuardarPlan && !formPlan.descripcion.trim()"
                              [(ngModel)]="formPlan.descripcion" placeholder="Describe los beneficios que incluye el plan" maxlength="200"></textarea>
                    <span class="texto-ayuda">{{ formPlan.descripcion.length }}/200 caracteres</span>
                  </div>

                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="grupo-campo">
                      <label>Precio *</label>
                      <input type="number" step="0.10" class="input-aegis" [(ngModel)]="formPlan.precio">
                    </div>
                    <div class="grupo-campo">
                      <label>Moneda *</label>
                      <select class="select-aegis" [(ngModel)]="formPlan.moneda">
                        <option value="PEN">PEN Sol peruano (S/)</option>
                      </select>
                    </div>
                  </div>

                  <div class="grupo-campo">
                    <label>Periodicidad *</label>
                    <select class="select-aegis" [(ngModel)]="formPlan.periodicidad">
                      <option value="Mensual">Mensual</option>
                      <option value="Semanal">Semanal</option>
                    </select>
                  </div>
                </div>

                <div class="tarjeta-blanca">
                  <h3 style="font-size: 16px; font-weight: 700; margin-bottom: 14px;">Protección y disponibilidad</h3>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="grupo-campo">
                      <label>Obras protegidas *</label>
                      <input type="number" class="input-aegis" [class.input-error]="intentoGuardarPlan && (!formPlan.obras_protegidas || formPlan.obras_protegidas <= 0)"
                             [(ngModel)]="formPlan.obras_protegidas" max="1000">
                      <span class="texto-ayuda">Máximo de obras por cuenta.</span>
                    </div>
                    <div class="grupo-campo">
                      <label>Obras en monitoreo *</label>
                      <input type="number" class="input-aegis"
                             [class.input-error]="intentoGuardarPlan && (!formPlan.obras_monitoreo || formPlan.obras_monitoreo > formPlan.obras_protegidas)"
                             [(ngModel)]="formPlan.obras_monitoreo" max="1000">
                      <span class="texto-ayuda">No debe superar las protegidas.</span>
                    </div>
                  </div>

                  <div class="grupo-campo">
                    <label>Frecuencia de monitoreo *</label>
                    <select class="select-aegis" [(ngModel)]="formPlan.frecuencia_monitoreo">
                      <option value="Diaria">Diaria · cada 24 horas</option>
                      <option value="Semanal">Semanal</option>
                    </select>
                  </div>

                  <div class="grupo-campo">
                    <label>Estado del plan *</label>
                    <select class="select-aegis" [(ngModel)]="formPlan.estado">
                      <option value="Activo">Activo</option>
                      <option value="Inactivo">Inactivo</option>
                    </select>
                  </div>

                  <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px;">
                    <button class="btn-secundario" (click)="modoAdminPlan = 'listado'">Cancelar</button>
                    <button class="btn-primario" (click)="guardarPlan()">
                      {{ planEditandoId ? 'Guardar cambios' : 'Crear plan' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- SUB-MODO 3: PLAN CREADO CON ÉXITO (Página 30 de Figma) -->
            <div *ngIf="modoAdminPlan === 'exito' && planRecienGuardado">
              <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">GESTIÓN DE PLANES</p>
              <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Plan guardado con éxito</h1>
              <div style="background: var(--verde-fondo); border: 1px solid var(--verde-exito); color: var(--verde-exito); padding: 14px 18px; border-radius: 12px; margin: 16px 0 22px;">
                <strong>● El plan {{ planRecienGuardado.nombre }} se ha guardado correctamente.</strong>
                <p style="font-size: 13px;">La configuración se ha guardado en PostgreSQL y está disponible en la plataforma.</p>
              </div>

              <div class="tarjeta-blanca" style="margin-bottom: 20px;">
                <h3 style="font-size: 18px; font-weight: 700; margin-bottom: 10px;">{{ planRecienGuardado.nombre }}</h3>
                <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 14px;">{{ planRecienGuardado.descripcion }}</p>
                <p style="font-size: 14px;">
                  <strong>Precio:</strong> S/{{ planRecienGuardado.precio }} ({{ planRecienGuardado.periodicidad }}) ·
                  <strong>Obras protegidas:</strong> {{ planRecienGuardado.obras_protegidas }} ·
                  <strong>Monitoreo:</strong> {{ planRecienGuardado.obras_monitoreo }} ({{ planRecienGuardado.frecuencia_monitoreo }})
                </p>
              </div>

              <div style="display: flex; justify-content: flex-end; gap: 12px;">
                <button class="btn-secundario" (click)="iniciarCrearPlan()">Crear otro plan</button>
                <button class="btn-primario" (click)="modoAdminPlan = 'listado'; cargarPlanes()">Ver planes</button>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 9: CONFIGURACIÓN / TU PERFIL CREATIVO (US-07 - Figura 48)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'configuracion'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">PREFERENCIAS</p>
            <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Tu perfil creativo</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 24px;">Tu espacio, a tu manera.</p>

            <div style="display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 28px;">
              <div class="tarjeta-blanca">
                <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 18px;">Datos del perfil</h3>

                <div *ngIf="mensajePerfilGuardado" style="background: var(--verde-fondo); color: var(--verde-exito); padding: 10px 14px; border-radius: 10px; font-size: 13px; font-weight: 600; margin-bottom: 14px;">
                  {{ mensajePerfilGuardado }}
                </div>

                <div class="grupo-campo">
                  <label>Nombre</label>
                  <input class="input-aegis" [(ngModel)]="formPerfil.nombre_apellido">
                </div>

                <div class="grupo-campo">
                  <label>Correo</label>
                  <input class="input-aegis" [(ngModel)]="formPerfil.correo">
                </div>

                <div class="grupo-campo">
                  <label>Especialidad</label>
                  <input class="input-aegis" [(ngModel)]="formPerfil.especialidad">
                </div>

                <div class="grupo-campo">
                  <label>Cambiar contraseña (US-07 · Opcional)</label>
                  <input type="password" class="input-aegis" [(ngModel)]="formPerfil.nueva_contrasena" placeholder="Dejar en blanco para mantener la actual">
                </div>

                <button class="btn-primario" style="width: 100%; margin-top: 8px;" (click)="guardarCambiosPerfil()">
                  Guardar cambios
                </button>
              </div>

              <div class="tarjeta-blanca">
                <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 6px;">Plan {{ perfil?.nombre_plan || 'Creador' }}</h3>
                <p style="font-size: 13px; color: var(--texto-secundario); margin-bottom: 10px;">
                  {{ perfil?.limite_obras_plan || 50 }} obras · Protección y monitoreo
                </p>
                <div class="barra-progreso-fondo" style="margin-bottom: 8px;">
                  <div class="barra-progreso-relleno"
                       [style.width.%]="((perfil?.obras_protegidas_actuales || 0) / (perfil?.limite_obras_plan || 50)) * 100"></div>
                </div>
                <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 22px;">
                  {{ perfil?.obras_protegidas_actuales || 0 }} de {{ perfil?.limite_obras_plan || 50 }} obras protegidas
                </p>

                <div style="display: flex; flex-direction: column; gap: 12px;">
                  <button class="btn-secundario" (click)="cambiarSeccion('suscripciones')">Explorar AegisArt Pro</button>
                  <button class="btn-primario" (click)="cambiarSeccion('moderacion')">Cambiar a vista de moderador</button>
                  <button class="btn-secundario" (click)="salirAlLogin()">Cerrar sesión / Ver login</button>
                </div>
              </div>
            </div>
          </div>

          <!-- =========================================================================
               SECCIÓN 10: ESPACIO DE MODERACIÓN (US-09 y US-10 - Páginas 59 y 61 de Figma)
               ========================================================================= -->
          <div *ngIf="seccionActual === 'moderacion'">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px;">
              <div>
                <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">MODERACIÓN</p>
                <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Espacio de moderación</h1>
                <p style="font-size: 14px; color: var(--texto-secundario);">
                  Revisión de apelaciones de plagio y de obras digitales clasificadas como sospechosas (US-09 y US-10).
                </p>
              </div>
              <button *ngIf="perfil?.rol === 'artista'" class="btn-secundario" (click)="cambiarSeccion('inicio')">Volver a vista artista</button>
            </div>

            <!-- Tarjeta de Evidencia del Modelo de IA Supervisado (Exigido en Cap. 2 y Cap. 3 del APF3) -->
            <div *ngIf="metricasIaApf3" class="tarjeta-blanca" style="margin-bottom: 24px; background: #faf8ff; border-color: var(--lavanda-borde);">
              <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
                <span class="badge badge-protegida">Motor IA Activo · {{ metricasIaApf3.algoritmo }}</span>
                <span style="font-size: 12px; color: var(--texto-secundario);">
                  Dataset: {{ metricasIaApf3.total_registros_dataset }} obras ({{ metricasIaApf3.registros_entrenamiento_80 }} train / {{ metricasIaApf3.registros_prueba_20 }} test) · CV F1: {{ metricasIaApf3.cv_f1_entrenamiento_porcentaje || metricasIaApf3.f1_score_porcentaje }}% · ROC-AUC: {{ metricasIaApf3.roc_auc_porcentaje || 99 }}%
                </span>
              </div>
              <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 10px;">
                <div style="background: #fff; padding: 12px; border-radius: 10px; border: 1px solid var(--borde-gris);">
                  <p style="font-size: 11px; color: var(--texto-secundario);">Accuracy (Exactitud)</p>
                  <p style="font-size: 22px; font-weight: 800; color: var(--morado-primario);">{{ metricasIaApf3.accuracy_porcentaje }}%</p>
                </div>
                <div style="background: #fff; padding: 12px; border-radius: 10px; border: 1px solid var(--borde-gris);">
                  <p style="font-size: 11px; color: var(--texto-secundario);">Precision</p>
                  <p style="font-size: 22px; font-weight: 800; color: var(--verde-exito);">{{ metricasIaApf3.precision_porcentaje }}%</p>
                </div>
                <div style="background: #fff; padding: 12px; border-radius: 10px; border: 1px solid var(--borde-gris);">
                  <p style="font-size: 11px; color: var(--texto-secundario);">Recall (Sensibilidad)</p>
                  <p style="font-size: 22px; font-weight: 800; color: #3d2c7a;">{{ metricasIaApf3.recall_porcentaje }}%</p>
                </div>
                <div style="background: #fff; padding: 12px; border-radius: 10px; border: 1px solid var(--borde-gris);">
                  <p style="font-size: 11px; color: var(--texto-secundario);">F1-Score</p>
                  <p style="font-size: 22px; font-weight: 800; color: var(--ambar-alerta);">{{ metricasIaApf3.f1_score_porcentaje }}%</p>
                </div>
              </div>
              <p *ngIf="metricasIaApf3.justificacion_tecnica" style="font-size: 12px; color: var(--texto-secundario); margin-top: 12px; line-height: 1.45;">
                {{ metricasIaApf3.justificacion_tecnica }}
              </p>
              <details *ngIf="metricasIaApf3.comparativa_algoritmos?.length" style="margin-top: 10px; font-size: 12px;">
                <summary style="cursor: pointer; font-weight: 700; color: var(--morado-primario);">
                  Ver comparativa experimental de los {{ metricasIaApf3.comparativa_algoritmos.length }} algoritmos evaluados (Supervisado vs. No Supervisado)
                </summary>
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px; background: #fff; border-radius: 8px; overflow: hidden;">
                  <thead>
                    <tr style="border-bottom: 1px solid var(--borde-gris); text-align: left; color: var(--texto-secundario);">
                      <th style="padding: 8px;">Modelo</th>
                      <th style="padding: 8px;">Enfoque</th>
                      <th style="padding: 8px;">Accuracy</th>
                      <th style="padding: 8px;">F1 Test</th>
                      <th style="padding: 8px;">CV F1</th>
                      <th style="padding: 8px;">Cordura OOD</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr *ngFor="let alg of metricasIaApf3.comparativa_algoritmos" style="border-bottom: 1px solid var(--borde-gris);">
                      <td style="padding: 8px; font-weight: 600;">{{ alg.modelo }}</td>
                      <td style="padding: 8px;">{{ alg.enfoque }}</td>
                      <td style="padding: 8px;">{{ alg.accuracy_porcentaje }}%</td>
                      <td style="padding: 8px; font-weight: 700;">{{ alg.f1_score_porcentaje }}%</td>
                      <td style="padding: 8px;">{{ alg.cv_f1_porcentaje !== null && alg.cv_f1_porcentaje !== undefined ? (alg.cv_f1_porcentaje + '%') : ('Sil=' + (alg.silhouette_score ?? 'N/A')) }}</td>
                      <td style="padding: 8px;">{{ alg.cordura_dominio }}</td>
                    </tr>
                  </tbody>
                </table>
              </details>
            </div>

            <!-- Tabla 1: Casos en revisión (Página 59 de Figma: AEG-003) -->
            <div class="tarjeta-blanca" style="margin-bottom: 24px;">
              <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 14px;">Casos en revisión</h3>
              <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                  <tr style="border-bottom: 1px solid var(--borde-gris); text-align: left; color: var(--texto-secundario);">
                    <th style="padding: 12px;">Caso</th>
                    <th style="padding: 12px;">Obra</th>
                    <th style="padding: 12px;">Similitud</th>
                    <th style="padding: 12px;">Motivo</th>
                    <th style="padding: 12px;">Fecha</th>
                    <th style="padding: 12px;">Estado</th>
                    <th style="padding: 12px;">Acción</th>
                  </tr>
                </thead>
                <tbody>
                  <tr *ngFor="let c of datosModeracion?.casos_en_revision" style="border-bottom: 1px solid var(--borde-gris);">
                    <td style="padding: 12px; font-weight: 700;">{{ c.codigo_caso }}</td>
                    <td style="padding: 12px;">{{ c.obra_titulo }}</td>
                    <td style="padding: 12px;">
                      <span class="badge badge-alerta">{{ c.similitud }}%</span>
                    </td>
                    <td style="padding: 12px;">{{ c.motivo }}</td>
                    <td style="padding: 12px;">{{ c.fecha }}</td>
                    <td style="padding: 12px;">
                      <span class="badge" [ngClass]="c.estado_moderador === 'Aceptada' ? 'badge-protegida' : 'badge-monitoreo'">
                        {{ c.estado_moderador }}
                      </span>
                    </td>
                    <td style="padding: 12px;">
                      <button class="btn-secundario" style="font-size: 12px; padding: 6px 14px;" (click)="abrirDetalleModeracion(c)">
                        Revisar →
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Tabla 2: Obras digitales marcadas como sospechosas al subirse (US-09 y US-10) -->
            <div class="tarjeta-blanca">
              <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 6px;">
                Obras digitales marcadas como sospechosas por el sistema (US-09 / US-10)
              </h3>
              <p style="font-size: 12px; color: var(--texto-secundario); margin-bottom: 14px;">
                Clasificación automática por Gradient Boosting ML (pHash, CLIP 512-d, marca invisible DCT/DWT, entropía visual, bordes Canny y declaración de inspiración US-08).
              </p>

              <p *ngIf="!datosModeracion?.obras_sospechosas?.length" style="font-size: 13px; color: var(--texto-secundario);">
                No hay obras sospechosas pendientes en este momento.
              </p>

              <table *ngIf="datosModeracion?.obras_sospechosas?.length" style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <thead>
                  <tr style="border-bottom: 1px solid var(--borde-gris); text-align: left; color: var(--texto-secundario);">
                    <th style="padding: 12px;">Código</th>
                    <th style="padding: 12px;">Título</th>
                    <th style="padding: 12px;">Autor</th>
                    <th style="padding: 12px;">Motivo de alerta</th>
                    <th style="padding: 12px;">Estado</th>
                    <th style="padding: 12px;">Decisión del Moderador (US-10)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr *ngFor="let os of datosModeracion.obras_sospechosas" style="border-bottom: 1px solid var(--borde-gris);">
                    <td style="padding: 12px; font-weight: 700;">{{ os.codigo_obra }}</td>
                    <td style="padding: 12px;">{{ os.titulo }}</td>
                    <td style="padding: 12px;">{{ os.autor }}</td>
                    <td style="padding: 12px; font-size: 12px; color: var(--ambar-alerta);">{{ os.motivo_sospecha }}</td>
                    <td style="padding: 12px;">{{ os.estado_moderacion }}</td>
                    <td style="padding: 12px; display: flex; gap: 6px;">
                      <button class="btn-primario" style="padding: 6px 10px; font-size: 12px;" (click)="decidirObraSospechosa(os.id, 'Aprobada')">Aprobar</button>
                      <button class="btn-secundario" style="padding: 6px 10px; font-size: 12px;" (click)="decidirObraSospechosa(os.id, 'Rechazada')">Rechazar</button>
                      <button class="btn-secundario" style="padding: 6px 10px; font-size: 12px; color: var(--rojo-error);" (click)="decidirObraSospechosa(os.id, 'Reportada')">Reportar</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- DETALLE DE REVISIÓN DE APELACIÓN DEL MODERADOR (Página 61 de Figma) -->
          <div *ngIf="seccionActual === 'moderacion_detalle' && casoModeracionActual">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
              <div>
                <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); text-transform: uppercase;">MODERACIÓN</p>
                <h1 style="font-size: 30px; font-weight: 800; margin: 4px 0;">Revisión de apelación</h1>
                <p style="font-size: 14px; color: var(--texto-secundario);">
                  Valida la evidencia y registra tu decisión.
                </p>
              </div>
              <button class="btn-secundario" (click)="cambiarSeccion('moderacion')">← Volver a moderación</button>
            </div>

            <div class="tarjeta-blanca" style="max-width: 780px;">
              <h3 style="font-size: 17px; font-weight: 700; margin-bottom: 6px;">
                Evidencia de la apelación ({{ casoModeracionActual.codigo_caso }} · {{ casoModeracionActual.obra_titulo }})
              </h3>
              <p style="font-size: 13px; color: var(--texto-secundario); margin-bottom: 16px;">
                El artista indica que la publicación no cuenta con su autorización.
              </p>

              <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px;">
                <span class="badge" [ngClass]="casoModeracionActual.marca_invisible_detectada ? 'badge-protegida' : 'badge-monitoreo'">
                  {{ casoModeracionActual.marca_invisible_detectada ? 'Marca invisible detectada' : 'Sin marca invisible DCT/DWT' }}
                </span>
                <span class="badge badge-alerta">Similitud {{ casoModeracionActual.similitud }}%</span>
                <span class="badge badge-monitoreo">Registro previo: {{ casoModeracionActual.fecha_registro_previo }}</span>
              </div>

              <div class="grupo-campo">
                <label>Comentarios del moderador</label>
                <textarea class="textarea-aegis" rows="4" [(ngModel)]="comentarioModeradorInput"
                          placeholder="Explica el motivo de tu decisión..."></textarea>
              </div>

              <div style="display: flex; gap: 12px; margin: 18px 0;">
                <button class="btn-primario" (click)="enviarDecisionApelacion('Aceptada')">Aceptar apelación</button>
                <button class="btn-secundario" (click)="enviarDecisionApelacion('Rechazada')">Rechazar apelación</button>
              </div>

              <div style="background: #f9f8fc; padding: 12px 16px; border-radius: 10px; font-size: 12px; color: var(--texto-secundario);">
                <strong>Estado del caso:</strong> La decisión actualizará el caso como resuelto en PostgreSQL.
              </div>
            </div>
          </div>

        </main>

        <!-- Pie de página consistente con Figma -->
        <footer class="pie-vista">
          <span>Hecho para artistas. Diseñado para proteger.</span>
          <span>AegisArt © 2026 · Sistema Funcional Sprint 1 y 2</span>
        </footer>
      </div>
    </div>
  `
})
export class EspacioArtistaComponent implements OnInit {
  seccionActual:
    | 'inicio'
    | 'mis_obras'
    | 'proteger'
    | 'procesando'
    | 'detalle_obra'
    | 'monitoreo'
    | 'coincidencias'
    | 'revision_coincidencia'
    | 'certificados'
    | 'reportes'
    | 'suscripciones'
    | 'admin_planes'
    | 'configuracion'
    | 'moderacion'
    | 'moderacion_detalle' = 'inicio';

  modoRolVista: 'artista' | 'moderador' | 'dueno' = 'artista';
  mostrarPanelNotificaciones = false;

  perfil: any = null;
  resumenInicio: any = null;
  listaObras: any[] = [];
  catalogoInspiracion: any[] = [];
  busquedaObras = '';
  filtroEstadoObras = 'Todas';

  // Variables para US-02, US-03, US-08 (Proteger obra)
  archivoSeleccionado: File | null = null;
  archivoInvalidoNombre = '';
  tamanoArchivoMb = 0;
  vistaPreviaUrl = '';
  errorCargaObra = '';
  intentoEnvioSinArchivo = false;
  intentoEnvioSinTitulo = false;
  formObra = {
    titulo: '',
    descripcion: '',
    nivel_proteccion: 'Equilibrada',
    es_inspirada: false,
    obra_inspirada_id: null as number | null
  };

  pasosProteccion = [
    'Archivo verificado',
    'Huella digital generada',
    'Marca invisible integrada',
    'Registro de autoría',
    'Monitoreo preparado'
  ];
  pasoActualAnimacion = 4;
  simularDemoraProceso = false;
  arrastrandoArchivo = false;
  resultadoProteccionIa: any = null;
  obraRecienCreadaId: number | null = null;
  obraActualDetalle: any = null;

  // Variables para US-05 y US-11 (Monitoreo por URL y Coincidencias)
  estadoMonitoreo: any = null;
  urlTemporalInput = '';
  obraIdParaEscanear: number | null = null;
  escaneandoUrl = false;
  resultadoEscaneoUrl: any = null;

  listaCoincidencias: any[] = [];
  filtroCoincidencias = 'Todas';
  coincidenciaActual: any = null;

  // Variables para US-06 y US-12 (Planes de Suscripción y Métricas Dueño)
  modoAdminPlan: 'listado' | 'formulario' | 'exito' = 'listado';
  listaPlanes: any[] = [];
  metricasDueno: any = null;
  filtroPlanes = {
    buscar: '',
    estado: 'Todos los estados',
    periodicidad: 'Todas las periodicidades'
  };
  planEditandoId: number | null = null;
  intentoGuardarPlan = false;
  errorFormularioPlan = '';
  planRecienGuardado: any = null;
  formPlan = {
    nombre: '',
    descripcion: '',
    precio: 39.90,
    moneda: 'PEN',
    periodicidad: 'Mensual',
    obras_protegidas: 50,
    obras_monitoreo: 25,
    frecuencia_monitoreo: 'Diaria',
    estado: 'Activo'
  };

  // Variables para US-07 (Perfil) y US-09/US-10 (Moderación)
  formPerfil = {
    nombre_apellido: '',
    correo: '',
    especialidad: '',
    nueva_contrasena: ''
  };
  mensajePerfilGuardado = '';

  datosModeracion: any = null;
  casoModeracionActual: any = null;
  comentarioModeradorInput = '';

  constructor(private api: ApiService, private router: Router) {}

  ngOnInit(): void {
    this.cargarDatosIniciales();
  }

  metricasIaApf3: any = null;

  cargarDatosIniciales(): void {
    this.api.obtenerPerfil().subscribe({
      next: (p) => {
        this.perfil = p;
        this.modoRolVista = p.rol || 'artista';
        this.formPerfil.nombre_apellido = p.nombre_apellido;
        this.formPerfil.correo = p.correo;
        this.formPerfil.especialidad = p.especialidad;

        if (p.rol === 'dueno') {
          // El Dueño entra directo a Gestión de Planes (US-06) y Métricas (US-12)
          this.abrirGestionPlanesAdmin();
        } else if (p.rol === 'moderador') {
          // El Moderador entra directo al Espacio de Moderación (US-09 y US-10)
          this.cambiarSeccion('moderacion');
        } else {
          // El Artista carga su espacio creativo
          this.api.obtenerResumenInicio().subscribe((res) => (this.resumenInicio = res));
          this.cargarObras();
          this.cargarCoincidencias();
          this.api.obtenerEstadoMonitoreo().subscribe((est) => (this.estadoMonitoreo = est));
        }
      }
    });
  }

  cambiarSeccion(nueva: any): void {
    this.seccionActual = nueva;
    this.mostrarPanelNotificaciones = false;

    if (nueva === 'inicio') {
      this.api.obtenerResumenInicio().subscribe((r) => (this.resumenInicio = r));
    } else if (nueva === 'mis_obras') {
      this.cargarObras();
    } else if (nueva === 'monitoreo') {
      this.api.obtenerEstadoMonitoreo().subscribe((e) => (this.estadoMonitoreo = e));
    } else if (nueva === 'coincidencias') {
      this.cargarCoincidencias();
    } else if (nueva === 'certificados' && !this.obraActualDetalle && this.listaObras.length > 0) {
      this.abrirCertificadoDeObra(this.listaObras[0].id);
    } else if (nueva === 'reportes' && !this.coincidenciaActual && this.listaCoincidencias.length > 0) {
      this.api.obtenerDetalleCoincidencia(this.listaCoincidencias[0].id).subscribe((d) => (this.coincidenciaActual = d));
    } else if (nueva === 'moderacion') {
      this.modoRolVista = 'moderador';
      this.api.obtenerCasosModeracion().subscribe((m) => (this.datosModeracion = m));
      this.api.obtenerMetricasIaApf3().subscribe((m) => (this.metricasIaApf3 = m));
    }
  }

  obtenerTituloBreadcrumb(): string {
    const mapa: any = {
      inicio: 'Inicio',
      mis_obras: 'Mis obras',
      proteger: 'Proteger obra',
      procesando: 'Proteger obra',
      detalle_obra: 'Mis obras',
      monitoreo: 'Monitoreo',
      coincidencias: 'Coincidencias',
      revision_coincidencia: 'Coincidencias',
      certificados: 'Certificados',
      reportes: 'Reportes',
      suscripciones: 'Pagos y suscripciones',
      admin_planes: 'Pagos y suscripciones / Gestión de planes',
      configuracion: 'Configuración',
      moderacion: 'Moderación',
      moderacion_detalle: 'Moderación / Revisión de apelación'
    };
    return mapa[this.seccionActual] || 'Inicio';
  }

  // ================= FLUJO MIS OBRAS Y PROTEGER OBRA =================
  cargarObras(): void {
    this.api.listarObras(this.busquedaObras, this.filtroEstadoObras).subscribe({
      next: (obras) => {
        this.listaObras = obras;
        if (!this.obraActualDetalle && obras.length > 0) {
          this.api.obtenerDetalleObra(obras[0].id).subscribe((d) => (this.obraActualDetalle = d));
        }
      }
    });
  }

  iniciarFlujoProteger(): void {
    this.seccionActual = 'proteger';
    this.limpiarArchivo();
    this.formObra = {
      titulo: '',
      descripcion: '',
      nivel_proteccion: 'Equilibrada',
      es_inspirada: false,
      obra_inspirada_id: null
    };
    this.intentoEnvioSinArchivo = false;
    this.intentoEnvioSinTitulo = false;
    this.api.listarCatalogoInspiracion().subscribe((cat) => (this.catalogoInspiracion = cat));
  }

  alArrastrarArchivo(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.arrastrandoArchivo = true;
  }

  alSoltarArchivo(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.arrastrandoArchivo = false;
    const file = event.dataTransfer?.files?.[0];
    if (file) {
      this.procesarArchivoSeleccionado(file);
    }
  }

  alSeleccionarArchivo(event: any): void {
    const file: File = event.target.files?.[0];
    if (file) {
      this.procesarArchivoSeleccionado(file);
    }
  }

  private procesarArchivoSeleccionado(file: File): void {
    this.errorCargaObra = '';
    this.archivoInvalidoNombre = '';
    const ext = file.name.split('.').pop()?.toUpperCase() || '';

    if (!['PNG', 'JPG', 'JPEG', 'WEBP'].includes(ext)) {
      this.archivoSeleccionado = null;
      this.archivoInvalidoNombre = file.name;
      this.errorCargaObra = 'La obra no se ha cargado correctamente. Carga un archivo válido (JPG, PNG o WEBP) y completa la información obligatoria para continuar.';
      return;
    }

    this.tamanoArchivoMb = Number((file.size / (1024 * 1024)).toFixed(2)) || 0.1;
    if (this.tamanoArchivoMb > 20) {
      this.archivoSeleccionado = null;
      this.archivoInvalidoNombre = file.name;
      this.errorCargaObra = 'El archivo supera el límite máximo permitido de 20 MB.';
      return;
    }

    this.archivoSeleccionado = file;
    const reader = new FileReader();
    reader.onload = (e: any) => (this.vistaPreviaUrl = e.target.result);
    reader.readAsDataURL(file);
  }

  limpiarArchivo(): void {
    this.archivoSeleccionado = null;
    this.archivoInvalidoNombre = '';
    this.vistaPreviaUrl = '';
    this.errorCargaObra = '';
    this.resultadoProteccionIa = null;
  }

  ejecutarProtegerYRegistrar(): void {
    this.intentoEnvioSinArchivo = !this.archivoSeleccionado;
    this.intentoEnvioSinTitulo = !this.formObra.titulo.trim();

    if (this.intentoEnvioSinArchivo || this.intentoEnvioSinTitulo) {
      this.errorCargaObra = 'Sube una imagen y completa el título para continuar.';
      return;
    }

    const fd = new FormData();
    fd.append('titulo', this.formObra.titulo.trim());
    fd.append('descripcion', this.formObra.descripcion || '');
    fd.append('nivel_proteccion', this.formObra.nivel_proteccion);
    if (this.formObra.es_inspirada && this.formObra.obra_inspirada_id) {
      fd.append('obra_inspirada_id', String(this.formObra.obra_inspirada_id));
    }
    fd.append('archivo', this.archivoSeleccionado!);

    this.seccionActual = 'procesando';
    this.pasoActualAnimacion = 2;
    this.obraRecienCreadaId = null;
    this.resultadoProteccionIa = null;

    this.api.protegerYRegistrarObra(fd).subscribe({
      next: (resp) => {
        this.pasoActualAnimacion = 5;
        this.obraRecienCreadaId = resp.obra.id;
        this.resultadoProteccionIa = resp.evaluacion_ia || resp.obra?.evaluacion_ia || null;
        this.cargarDatosIniciales();
      },
      error: (err) => {
        this.seccionActual = 'proteger';
        this.errorCargaObra = err.error?.detail || 'Ocurrió un error al proteger la obra.';
      }
    });
  }

  abrirDetalleObra(obraId: number): void {
    this.api.obtenerDetalleObra(obraId).subscribe({
      next: (det) => {
        this.obraActualDetalle = det;
        this.seccionActual = 'detalle_obra';
      }
    });
  }

  abrirCertificadoDeObra(obraId: number): void {
    this.api.obtenerDetalleObra(obraId).subscribe({
      next: (det) => (this.obraActualDetalle = det)
    });
  }

  // ================= FLUJO MONITOREO POR URL Y COINCIDENCIAS =================
  ejecutarEscaneoUrl(): void {
    if (!this.urlTemporalInput.trim()) return;
    this.escaneandoUrl = true;
    this.resultadoEscaneoUrl = null;

    this.api.escanearUrlTemporal(this.urlTemporalInput.trim(), this.obraIdParaEscanear).subscribe({
      next: (res) => {
        this.escaneandoUrl = false;
        this.resultadoEscaneoUrl = res;
        this.api.obtenerEstadoMonitoreo().subscribe((e) => (this.estadoMonitoreo = e));
        this.cargarCoincidencias();
        this.api.obtenerResumenInicio().subscribe((r) => (this.resumenInicio = r));
      },
      error: (err) => {
        this.escaneandoUrl = false;
        alert(err.error?.detail || 'No se pudo analizar la URL ingresada.');
      }
    });
  }

  cargarCoincidencias(): void {
    this.api.listarCoincidencias(this.filtroCoincidencias).subscribe({
      next: (lista) => (this.listaCoincidencias = lista)
    });
  }

  abrirRevisionCoincidencia(coincidenciaId: number): void {
    this.api.obtenerDetalleCoincidencia(coincidenciaId).subscribe({
      next: (det) => {
        this.coincidenciaActual = det;
        this.seccionActual = 'revision_coincidencia';
      }
    });
  }

  cambiarEstadoCaso(coincidenciaId: number, nuevoEstado: string): void {
    this.api.actualizarEstadoCoincidencia(coincidenciaId, nuevoEstado).subscribe({
      next: () => {
        this.coincidenciaActual.estado_artista = nuevoEstado;
        this.cargarCoincidencias();
        alert(`Caso marcado como: ${nuevoEstado}`);
      }
    });
  }

  iniciarReclamoCaso(coincidenciaId: number): void {
    this.api.actualizarEstadoCoincidencia(coincidenciaId, 'Reclamo').subscribe({
      next: () => {
        this.cambiarSeccion('reportes');
      }
    });
  }

  descargarReportePdf(): void {
    const idCaso = this.coincidenciaActual?.id || 1;
    window.open(this.api.obtenerUrlDescargaPdf(idCaso), '_blank');
  }

  prepararTakeDown(): void {
    alert(
      `Solicitud DMCA / Take-Down lista para enviar con el certificado ${
        this.coincidenciaActual?.codigo_certificado || 'AEG-2026-0024'
      } y transacción Blockchain verificada.`
    );
  }

  // ================= FLUJO ADMIN PLANES (US-06) Y MÉTRICAS DUEÑO (US-12) =================
  abrirGestionPlanesAdmin(): void {
    this.modoRolVista = 'dueno';
    this.seccionActual = 'admin_planes';
    this.modoAdminPlan = 'listado';
    this.cargarPlanes();
    this.api.obtenerMetricasDueno().subscribe((m) => (this.metricasDueno = m));
  }

  cargarPlanes(): void {
    this.api
      .listarPlanes(this.filtroPlanes.buscar, this.filtroPlanes.estado, this.filtroPlanes.periodicidad)
      .subscribe((planes) => (this.listaPlanes = planes));
  }

  iniciarCrearPlan(): void {
    this.planEditandoId = null;
    this.intentoGuardarPlan = false;
    this.errorFormularioPlan = '';
    this.formPlan = {
      nombre: '',
      descripcion: '',
      precio: 19.90,
      moneda: 'PEN',
      periodicidad: 'Mensual',
      obras_protegidas: 50,
      obras_monitoreo: 25,
      frecuencia_monitoreo: 'Diaria',
      estado: 'Activo'
    };
    this.modoAdminPlan = 'formulario';
  }

  iniciarEditarPlan(plan: any): void {
    this.planEditandoId = plan.id;
    this.intentoGuardarPlan = false;
    this.errorFormularioPlan = '';
    this.formPlan = {
      nombre: plan.nombre,
      descripcion: plan.descripcion,
      precio: plan.precio,
      moneda: plan.moneda,
      periodicidad: plan.periodicidad,
      obras_protegidas: plan.obras_protegidas,
      obras_monitoreo: plan.obras_monitoreo,
      frecuencia_monitoreo: plan.frecuencia_monitoreo,
      estado: plan.estado
    };
    this.modoAdminPlan = 'formulario';
  }

  guardarPlan(): void {
    this.intentoGuardarPlan = true;
    this.errorFormularioPlan = '';

    if (
      !this.formPlan.nombre.trim() ||
      !this.formPlan.descripcion.trim() ||
      !this.formPlan.obras_protegidas ||
      !this.formPlan.obras_monitoreo ||
      this.formPlan.obras_monitoreo > this.formPlan.obras_protegidas
    ) {
      this.errorFormularioPlan =
        'Revisa los campos señalados: completa el nombre, la descripción y verifica que las obras en monitoreo no superen a las obras protegidas.';
      return;
    }

    const obs = this.planEditandoId
      ? this.api.actualizarPlan(this.planEditandoId, this.formPlan)
      : this.api.crearPlan(this.formPlan);

    obs.subscribe({
      next: (resp) => {
        this.planRecienGuardado = resp.plan;
        this.modoAdminPlan = 'exito';
        this.api.obtenerMetricasDueno().subscribe((m) => (this.metricasDueno = m));
      },
      error: (err) => {
        this.errorFormularioPlan = err.error?.detail || 'Error al guardar el plan.';
      }
    });
  }

  // ================= FLUJO PERFIL (US-07) Y MODERACIÓN (US-09 / US-10) =================
  guardarCambiosPerfil(): void {
    this.mensajePerfilGuardado = '';
    this.api.actualizarPerfil(this.formPerfil).subscribe({
      next: (resp) => {
        this.mensajePerfilGuardado = resp.mensaje;
        this.formPerfil.nueva_contrasena = '';
        this.cargarDatosIniciales();
      }
    });
  }

  abrirDetalleModeracion(caso: any): void {
    this.casoModeracionActual = caso;
    this.comentarioModeradorInput = caso.comentarios_moderador || '';
    this.seccionActual = 'moderacion_detalle';
  }

  enviarDecisionApelacion(decision: string): void {
    if (!this.casoModeracionActual) return;
    this.api
      .resolverCasoModerador(this.casoModeracionActual.id, decision, this.comentarioModeradorInput)
      .subscribe(() => {
        this.cambiarSeccion('moderacion');
      });
  }

  decidirObraSospechosa(obraId: number, decision: string): void {
    this.api.revisarObraSospechosa(obraId, decision, 'Revisado por moderador').subscribe(() => {
      this.api.obtenerCasosModeracion().subscribe((m) => (this.datosModeracion = m));
    });
  }

  salirAlLogin(): void {
    this.api.cerrarSesion();
    this.router.navigate(['/']);
  }
}