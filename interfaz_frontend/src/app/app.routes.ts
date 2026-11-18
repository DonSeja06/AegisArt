import { Routes } from '@angular/router';
import { AccesoPublicoComponent } from './componentes/publico/acceso-publico.component';
import { EspacioArtistaComponent } from './componentes/artista/espacio-artista.component';

export const routes: Routes = [
  { path: '', component: AccesoPublicoComponent },
  { path: 'espacio', component: EspacioArtistaComponent },
  { path: '**', redirectTo: '' }
];