import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../servicios/api.service';

@Component({
  selector: 'app-acceso-publico',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <!-- ================= VISTA 1: LANDING DE BIENVENIDA (Figura 34) ================= -->
    <div *ngIf="modoVista === 'bienvenida'" style="min-height: 100vh; background: #ffffff; display: flex; flex-direction: column;">
      <!-- Barra superior Landing -->
      <header style="display: flex; justify-content: space-between; align-items: center; padding: 22px 64px; border-bottom: 1px solid #f0edf6;">
        <div class="marca-logo" style="margin: 0;">
          <span class="icono-check-logo">✓</span>
          <span>Aegis<span style="color: var(--morado-primario);">Art</span></span>
        </div>
        <nav style="display: flex; gap: 36px; font-size: 14px; font-weight: 500; color: var(--texto-secundario);">
          <a (click)="irALogin()" style="cursor: pointer;">Protección</a>
          <a (click)="irALogin()" style="cursor: pointer;">Monitoreo</a>
          <a (click)="irALogin()" style="cursor: pointer;">Autoría</a>
        </nav>
        <button class="btn-secundario" (click)="irALogin()">Iniciar sesión →</button>
      </header>

      <!-- Hero Principal -->
      <main style="flex: 1; max-width: 1220px; width: 100%; margin: 0 auto; padding: 56px 32px; display: grid; grid-template-columns: 1.05fr 0.95fr; gap: 48px; align-items: center;">
        <div>
          <p style="font-size: 11px; font-weight: 700; letter-spacing: 1.2px; color: var(--morado-primario); text-transform: uppercase; margin-bottom: 14px;">
            EL FUTURO DE TU ARTE ES TUYO
          </p>
          <h1 style="font-size: 54px; font-weight: 800; line-height: 1.08; color: #161026; margin-bottom: 20px;">
            Protege tu arte.<br>
            <span style="color: #8c65f7;">Demuestra<br>que es tuyo.</span>
          </h1>
          <p style="font-size: 16px; line-height: 1.6; color: var(--texto-secundario); max-width: 500px; margin-bottom: 30px;">
            Tu creatividad merece algo más que una marca de agua. Un espacio para explorar la protección de tus obras, detectar coincidencias y respaldar tu autoría.
          </p>
          <div style="display: flex; gap: 14px; margin-bottom: 16px;">
            <button class="btn-primario" style="padding: 14px 28px; font-size: 15px;" (click)="modoVista = 'registro'">
              Proteger mi arte →
            </button>
            <button class="btn-secundario" style="padding: 14px 26px; font-size: 15px;" (click)="irALogin()">
              Explorar la plataforma →
            </button>
          </div>
          <p style="font-size: 12px; color: var(--texto-secundario);">Tu estilo intacto. Tu identidad siempre.</p>
        </div>

        <!-- Ilustración Derecha estilo Pixel Art Nocturno con tarjeta flotante -->
        <div style="position: relative;">
          <div style="background: linear-gradient(180deg, #4b338c 0%, #6143b0 65%, #37236b 100%); height: 360px; border-radius: 22px; position: relative; overflow: hidden; box-shadow: 0 20px 45px rgba(75,51,140,0.22);">
            <!-- Estrellas y nubes decorativas -->
            <div style="position: absolute; top: 45px; left: 80px; width: 6px; height: 6px; background: #cbbcff; border-radius: 50%;"></div>
            <div style="position: absolute; top: 85px; right: 130px; width: 8px; height: 8px; background: #e1d8ff; border-radius: 50%;"></div>
            <div style="position: absolute; bottom: 95px; left: 40px; right: 40px; height: 65px; background: rgba(215, 206, 255, 0.85); border-radius: 30px; filter: blur(1px);"></div>
            <div style="position: absolute; bottom: 0; left: 0; right: 0; height: 95px; background: #38216b; clip-path: polygon(0 40%, 20% 10%, 45% 45%, 75% 15%, 100% 35%, 100% 100%, 0 100%);"></div>
          </div>

          <!-- Icono Check flotante superior derecho -->
          <div style="position: absolute; top: -18px; right: -14px; width: 64px; height: 64px; border-radius: 16px; background: #9b7bf7; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; box-shadow: 0 10px 24px rgba(123,77,255,0.35);">
            ✓
          </div>

          <!-- Tarjeta flotante inferior izquierda -->
          <div class="tarjeta-blanca" style="position: absolute; bottom: -22px; left: -20px; padding: 18px 24px; width: 280px; box-shadow: 0 12px 30px rgba(0,0,0,0.08);">
            <span class="badge badge-protegida" style="margin-bottom: 8px;">Obra original</span>
            <p style="font-size: 13px; color: var(--texto-secundario);">La imaginación no tiene dueño.</p>
            <p style="font-size: 14px; font-weight: 700; color: var(--texto-principal);">Tu obra sí.</p>
          </div>
        </div>
      </main>

      <!-- 3 Columnas inferiores de Propuesta de Valor -->
      <section style="max-width: 1220px; width: 100%; margin: 20px auto 48px; padding: 28px 32px 0; border-top: 1px solid var(--borde-gris); display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px;">
        <div>
          <h3 style="font-size: 15px; font-weight: 700; margin-bottom: 6px;">Protección contra IA</h3>
          <p style="font-size: 13px; color: var(--texto-secundario);">Tu estilo no se presta. Perturbación adversarial y marca invisible DCT/DWT.</p>
        </div>
        <div>
          <h3 style="font-size: 15px; font-weight: 700; margin-bottom: 6px;">Detección de plagio</h3>
          <p style="font-size: 13px; color: var(--texto-secundario);">Siempre que alguien copie. Comparación perceptual imageHash y semántica CLIP.</p>
        </div>
        <div>
          <h3 style="font-size: 15px; font-weight: 700; margin-bottom: 6px;">Certificación de autoría</h3>
          <p style="font-size: 13px; color: var(--texto-secundario);">Tu firma, respaldada. Registro verificable en Smart Contract con Solidity y Hardhat.</p>
        </div>
      </section>
    </div>

    <!-- ================= VISTAS DE ACCESO: LOGIN, REGISTRO, ÉXITO Y RECUPERAR (Figuras 35, 36, 37) ================= -->
    <div *ngIf="modoVista !== 'bienvenida'" style="min-height: 100vh; display: grid; grid-template-columns: 1fr 1fr;">
      
      <!-- Panel Izquierdo Artístico Morado Oscuro -->
      <div style="background-color: var(--morado-oscuro); color: #ffffff; padding: 42px 56px; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="font-size: 22px; font-weight: 800; cursor: pointer;" (click)="modoVista = 'bienvenida'">
          Aegis<span style="color: #a688fa;">Art</span>
        </div>

        <div style="my: auto; display: flex; flex-direction: column; align-items: center;">
          <!-- Ilustración decorativa según pantalla -->
          <div style="width: 100%; max-width: 410px; height: 370px; border-radius: 18px; overflow: hidden; margin-bottom: 28px; border: 1px solid rgba(255,255,255,0.12); background: radial-gradient(circle at 50% 40%, #8c52ff 0%, #2a164d 55%, #120824 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 24px; text-align: center; position: relative;">
            <div *ngIf="modoVista === 'login'" style="font-size: 64px; margin-bottom: 12px;">🦝✨</div>
            <div *ngIf="modoVista === 'registro' || modoVista === 'registro_exito'" style="font-size: 64px; margin-bottom: 12px;">🪐🎨</div>
            <div *ngIf="modoVista === 'recuperar'" style="font-size: 64px; margin-bottom: 12px;">🌌🌙</div>
            <p style="font-size: 14px; color: #e2d9ff; font-weight: 500;">
              {{ modoVista === 'login' ? 'Espacio creativo protegido · To: BEANIE' : (modoVista === 'recuperar' ? 'Noche estrellada · Acceso seguro' : 'Universo artístico · Identidad blindada') }}
            </p>
          </div>

          <div style="width: 100%; max-width: 410px;">
            <h2 style="font-size: 38px; font-weight: 800; line-height: 1.12; margin-bottom: 12px;">
              Tu creatividad.<br>Tu identidad.<br>Siempre tuya.
            </h2>
            <p style="font-size: 14px; color: #c5b8e8;">Un espacio seguro para todo lo que imaginas.</p>
          </div>
        </div>

        <div style="font-size: 12px; color: #9c8ec4;">© 2026 AegisArt · Protección de Propiedad Intelectual</div>
      </div>

      <!-- Panel Derecho de Formularios -->
      <div style="background: #ffffff; padding: 42px 64px; display: flex; flex-direction: column; justify-content: center; overflow-y: auto;">
        <div style="max-width: 440px; width: 100%; margin: 0 auto;">
          
          <a (click)="modoVista = (modoVista === 'recuperar' ? 'login' : 'bienvenida')"
             style="display: inline-block; font-size: 13px; color: var(--texto-secundario); cursor: pointer; margin-bottom: 18px;">
            ← {{ modoVista === 'recuperar' ? 'Volver a iniciar sesión' : 'Volver al inicio' }}
          </a>

          <div style="font-size: 24px; font-weight: 800; margin-bottom: 18px;">
            Aegis<span style="color: var(--morado-primario);">Art</span>
          </div>

          <!-- Conmutador Iniciar sesión / Registrarse -->
          <div *ngIf="modoVista === 'login' || modoVista === 'registro'"
               style="display: grid; grid-template-columns: 1fr 1fr; background: #f4f1fa; padding: 4px; border-radius: 12px; margin-bottom: 24px;">
            <button (click)="cambiarModo('login')"
                    [style.background]="modoVista === 'login' ? 'var(--morado-primario)' : 'transparent'"
                    [style.color]="modoVista === 'login' ? '#fff' : 'var(--texto-principal)'"
                    style="border: none; padding: 10px; border-radius: 9px; font-weight: 600; font-size: 13px; cursor: pointer;">
              Iniciar sesión
            </button>
            <button (click)="cambiarModo('registro')"
                    [style.background]="modoVista === 'registro' ? 'var(--morado-primario)' : 'transparent'"
                    [style.color]="modoVista === 'registro' ? '#fff' : 'var(--texto-principal)'"
                    style="border: none; padding: 10px; border-radius: 9px; font-weight: 600; font-size: 13px; cursor: pointer;">
              Registrarse
            </button>
          </div>

          <!-- SUB-VISTA A: INICIAR SESIÓN (US-01) -->
          <div *ngIf="modoVista === 'login'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 6px;">
              TU CREATIVIDAD TE ESPERA
            </p>
            <h1 style="font-size: 28px; font-weight: 800; margin-bottom: 6px;">Te damos la bienvenida</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); margin-bottom: 22px;">Ingresa a tu espacio y continúa creando.</p>

            <div *ngIf="mensajeErrorLogin" style="background: var(--rojo-fondo); border: 1px solid var(--rojo-error); color: var(--rojo-error); padding: 10px 14px; border-radius: 10px; font-size: 13px; margin-bottom: 16px;">
              {{ mensajeErrorLogin }}
            </div>

            <div class="grupo-campo">
              <label>Correo electrónico</label>
              <input type="email" class="input-aegis" [(ngModel)]="formLogin.correo" placeholder="tu@correo.com">
            </div>

            <div class="grupo-campo">
              <label>Contraseña</label>
              <input type="password" class="input-aegis" [(ngModel)]="formLogin.contrasena" placeholder="Al menos 8 caracteres">
              <div style="text-align: right; margin-top: 4px;">
                <a (click)="modoVista = 'recuperar'" style="font-size: 12px; color: var(--morado-primario); font-weight: 600; cursor: pointer;">
                  ¿Olvidaste tu contraseña?
                </a>
              </div>
            </div>

            <button class="btn-primario" style="width: 100%; margin-top: 8px; padding: 13px;" (click)="ejecutarLogin()">
              Iniciar sesión →
            </button>

            <p style="text-align: center; font-size: 13px; color: var(--texto-secundario); margin-top: 16px;">
              ¿Es tu primera vez aquí?
              <a (click)="cambiarModo('registro')" style="color: var(--morado-primario); font-weight: 600; cursor: pointer;">Crear cuenta</a>
            </p>

            <div style="margin-top: 24px; padding: 14px 16px; background: #f8f6fc; border-radius: 12px;">
              <p style="font-size: 13px; font-weight: 700; color: var(--texto-principal); margin-bottom: 2px;">
                Plataforma AegisArt
              </p>
              <p style="font-size: 12px; color: var(--texto-secundario);">
                Ingresa con tu cuenta de Artista, Moderador o Administración según tu rol asignado.
              </p>
            </div>
          </div>

          <!-- SUB-VISTA B: CREA TU CUENTA CON VALIDACIONES EN ROJO (US-01) -->
          <div *ngIf="modoVista === 'registro'">
            <p style="font-size: 11px; font-weight: 700; color: var(--texto-secundario); letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 6px;">
              EMPIEZA TU ESPACIO CREATIVO
            </p>
            <h1 style="font-size: 28px; font-weight: 800; margin-bottom: 18px;">Crea tu cuenta</h1>

            <div *ngIf="erroresRegistro.general" style="background: var(--rojo-fondo); border: 1px solid var(--rojo-error); color: var(--rojo-error); padding: 10px 14px; border-radius: 10px; font-size: 13px; margin-bottom: 14px;">
              {{ erroresRegistro.general }}
            </div>

            <div class="grupo-campo">
              <label>Nombre y apellido</label>
              <input type="text" class="input-aegis" [class.input-error]="erroresRegistro.nombre"
                     [(ngModel)]="formRegistro.nombre_apellido" placeholder="Valentina Torres" maxlength="120">
              <span *ngIf="erroresRegistro.nombre" class="texto-error">{{ erroresRegistro.nombre }}</span>
            </div>

            <div class="grupo-campo">
              <label>DNI</label>
              <input type="text" class="input-aegis" [class.input-error]="erroresRegistro.dni"
                     [(ngModel)]="formRegistro.dni" placeholder="8 dígitos, sin espacios" maxlength="8">
              <span *ngIf="erroresRegistro.dni" class="texto-error">{{ erroresRegistro.dni }}</span>
            </div>

            <div class="grupo-campo">
              <label>Correo electrónico</label>
              <input type="email" class="input-aegis" [class.input-error]="erroresRegistro.correo"
                     [(ngModel)]="formRegistro.correo" placeholder="tu@correo.com">
              <span *ngIf="erroresRegistro.correo" class="texto-error">{{ erroresRegistro.correo }}</span>
            </div>

            <div class="grupo-campo">
              <label>Celular</label>
              <input type="text" class="input-aegis" [class.input-error]="erroresRegistro.celular"
                     [(ngModel)]="formRegistro.celular" placeholder="+51 9XXXXXXXX">
              <span *ngIf="erroresRegistro.celular" class="texto-error">{{ erroresRegistro.celular }}</span>
            </div>

            <div class="grupo-campo">
              <label>Contraseña</label>
              <input type="password" class="input-aegis" [class.input-error]="erroresRegistro.contrasena"
                     [(ngModel)]="formRegistro.contrasena" placeholder="Al menos 8 caracteres">
              <span *ngIf="erroresRegistro.contrasena" class="texto-error">{{ erroresRegistro.contrasena }}</span>
            </div>

            <button class="btn-primario" style="width: 100%; margin-top: 8px; padding: 13px;" (click)="ejecutarRegistro()">
              Crear cuenta →
            </button>

            <p style="text-align: center; font-size: 13px; color: var(--texto-secundario); margin-top: 14px;">
              ¿Ya tienes cuenta?
              <a (click)="cambiarModo('login')" style="color: var(--morado-primario); font-weight: 600; cursor: pointer;">Iniciar sesión</a>
            </p>
          </div>

          <!-- SUB-VISTA C: ¡REGISTRO EXITOSO! (Página 4 del PDF de Figma) -->
          <div *ngIf="modoVista === 'registro_exito'">
            <p style="font-size: 11px; font-weight: 700; color: var(--morado-primario); letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 6px;">
              TU ESPACIO CREATIVO ESTÁ LISTO
            </p>
            <h1 style="font-size: 28px; font-weight: 800; margin-bottom: 10px;">¡Registro exitoso!</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); line-height: 1.5; margin-bottom: 20px;">
              Bienvenida, {{ usuarioRecienCreado?.nombre_apellido?.split(' ')[0] }}. Tu cuenta de AegisArt se creó correctamente. Ya puedes empezar a proteger tus obras.
            </p>

            <div style="background: #f8f6fe; border: 1px solid var(--lavanda-borde); border-radius: 14px; padding: 16px; margin-bottom: 20px;">
              <p style="font-weight: 700; font-size: 15px;">{{ usuarioRecienCreado?.nombre_apellido }}</p>
              <p style="font-size: 13px; color: var(--texto-secundario); margin-bottom: 12px;">{{ usuarioRecienCreado?.correo }}</p>
              <p style="font-size: 13px; font-weight: 600; color: var(--morado-primario);">Tu primera obra, siempre tuya.</p>
              <p style="font-size: 12px; color: var(--texto-secundario);">Entra a tu espacio y registra tu primera creación.</p>
            </div>

            <button class="btn-primario" style="width: 100%; padding: 13px;" (click)="entrarAlEspacio()">
              Ir a mi espacio →
            </button>
            <p style="text-align: center; font-size: 12px; color: var(--texto-secundario); margin-top: 12px;">
              Gracias por confiar en AegisArt.
            </p>
          </div>

          <!-- SUB-VISTA D: RECUPERA TU CUENTA (US-07 - Figura 37) -->
          <div *ngIf="modoVista === 'recuperar'">
            <p style="font-size: 11px; font-weight: 700; color: var(--morado-primario); letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 6px;">
              RECUPERA EL ACCESO
            </p>
            <h1 style="font-size: 28px; font-weight: 800; margin-bottom: 8px;">Recupera tu cuenta</h1>
            <p style="font-size: 14px; color: var(--texto-secundario); line-height: 1.5; margin-bottom: 22px;">
              Escribe el correo asociado a tu cuenta. Te enviaremos un enlace para restablecer tu contraseña.
            </p>

            <div class="grupo-campo">
              <label>Correo electrónico</label>
              <input type="email" class="input-aegis" [(ngModel)]="formRecuperar.correo" placeholder="Ingresa tu correo electrónico">
            </div>

            <button class="btn-primario" style="width: 100%; padding: 13px; margin-bottom: 18px;" (click)="enviarEnlaceRecuperacion()">
              Enviar enlace de recuperación →
            </button>

            <div *ngIf="mensajeRecuperacion" style="background: var(--verde-fondo); border: 1px solid var(--verde-exito); color: var(--verde-exito); padding: 12px; border-radius: 10px; font-size: 13px; margin-bottom: 16px;">
              <p style="font-weight: 600;">{{ mensajeRecuperacion }}</p>
              <!-- Cambio directo de contraseña para demostrar US-07 en vivo -->
              <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(18,156,104,0.2);">
                <label style="display:block; font-size: 12px; margin-bottom: 4px; color: var(--texto-principal);">Nueva contraseña (mínimo 8 caracteres):</label>
                <input type="password" class="input-aegis" [(ngModel)]="formRecuperar.nueva_contrasena" placeholder="Nueva contraseña segura">
                <button class="btn-primario" style="width: 100%; margin-top: 8px; padding: 10px;" (click)="confirmarNuevaContrasena()">
                  Actualizar contraseña ahora
                </button>
              </div>
            </div>

            <div style="background: #f9f8fc; border-radius: 12px; padding: 14px;">
              <p style="font-size: 13px; font-weight: 700; margin-bottom: 4px;">¿No recibiste el correo?</p>
              <p style="font-size: 12px; color: var(--texto-secundario);">
                Si el correo está registrado, recibirás un enlace válido durante 15 minutos.
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  `
})
export class AccesoPublicoComponent {
  modoVista: 'bienvenida' | 'login' | 'registro' | 'registro_exito' | 'recuperar' = 'bienvenida';

  formLogin = { correo: '', contrasena: '' };
  mensajeErrorLogin = '';

  formRegistro = {
    nombre_apellido: '',
    dni: '',
    correo: '',
    celular: '',
    contrasena: ''
  };
  erroresRegistro: any = {};
  usuarioRecienCreado: any = null;

  formRecuperar = { correo: '', nueva_contrasena: '', token: '' };
  mensajeRecuperacion = '';

  constructor(private api: ApiService, private router: Router) {}

  irALogin(): void {
    this.modoVista = 'login';
    this.mensajeErrorLogin = '';
  }

  cambiarModo(modo: 'login' | 'registro'): void {
    this.modoVista = modo;
    this.mensajeErrorLogin = '';
    this.erroresRegistro = {};
  }

  ejecutarLogin(): void {
    this.mensajeErrorLogin = '';
    this.api.iniciarSesion(this.formLogin).subscribe({
      next: (resp) => {
        this.api.guardarSesion(resp.token_acceso, resp.usuario);
        this.router.navigate(['/espacio']);
      },
      error: (err) => {
        this.mensajeErrorLogin = err.error?.detail || 'Credenciales inválidas. Verifica tu correo y contraseña.';
      }
    });
  }

  accesoRapido(correoDemo: string): void {
    this.formLogin.correo = correoDemo;
    this.formLogin.contrasena = 'aegisart123';
    this.ejecutarLogin();
  }

  ejecutarRegistro(): void {
    this.erroresRegistro = {};
    let hayError = false;

    if (!this.formRegistro.nombre_apellido || this.formRegistro.nombre_apellido.trim().length < 3) {
      this.erroresRegistro.nombre = 'Ingresa tu nombre y apellido.';
      hayError = true;
    }
    if (!/^\d{8}$/.test(this.formRegistro.dni.trim())) {
      this.erroresRegistro.dni = 'Ingresa 8 dígitos, sin espacios.';
      hayError = true;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.formRegistro.correo.trim())) {
      this.erroresRegistro.correo = 'Ingresa un correo válido, como tu@correo.com.';
      hayError = true;
    }
    const celLimpio = this.formRegistro.celular.replace(/\s+/g, '').replace(/^\+51/, '');
    if (!/^9\d{8}$/.test(celLimpio)) {
      this.erroresRegistro.celular = 'Ingresa 9 dígitos después de +51, empezando por 9.';
      hayError = true;
    }
    if (!this.formRegistro.contrasena || this.formRegistro.contrasena.length < 8) {
      const cant = this.formRegistro.contrasena ? this.formRegistro.contrasena.length : 0;
      this.erroresRegistro.contrasena = `Usa al menos 8 caracteres; ingresaste ${cant}.`;
      hayError = true;
    }

    if (hayError) return;

    this.api.registrarUsuario(this.formRegistro).subscribe({
      next: (resp) => {
        this.api.guardarSesion(resp.token_acceso, resp.usuario);
        this.usuarioRecienCreado = resp.usuario;
        this.modoVista = 'registro_exito';
      },
      error: (err) => {
        this.erroresRegistro.general = err.error?.detail || 'No se pudo completar el registro. Verifica los datos.';
      }
    });
  }

  entrarAlEspacio(): void {
    this.router.navigate(['/espacio']);
  }

  enviarEnlaceRecuperacion(): void {
    if (!this.formRecuperar.correo) return;
    this.api.solicitarRecuperacion(this.formRecuperar.correo).subscribe({
      next: (resp) => {
        this.mensajeRecuperacion = resp.mensaje;
        this.formRecuperar.token = resp.token_demo_prototipo || '';
      }
    });
  }

  confirmarNuevaContrasena(): void {
    if (!this.formRecuperar.nueva_contrasena || this.formRecuperar.nueva_contrasena.length < 8) {
      alert('La nueva contraseña debe tener al menos 8 caracteres.');
      return;
    }
    this.api.restablecerContrasena({
      correo: this.formRecuperar.correo,
      nueva_contrasena: this.formRecuperar.nueva_contrasena,
      token_recuperacion: this.formRecuperar.token
    }).subscribe({
      next: (resp) => {
        alert(resp.mensaje);
        this.mensajeRecuperacion = '';
        this.modoVista = 'login';
      },
      error: (err) => alert(err.error?.detail || 'Error al actualizar la contraseña.')
    });
  }
}