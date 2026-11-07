# Actividad-16
# 202216
# Omar Reyes Gonzalez


##  Propósito del Proyecto

En la computación de alto rendimiento (HPC) y la predicción meteorológica moderna, modelar fenómenos físicos sobre grandes regiones geográficas requiere millones de cálculos por segundo. Este proyecto implementa la técnica de **Descomposición de Dominio con Celdas Fantasma (*Ghost Cells*)** para:

1. **Dividir la carga computacional** de una malla espacial entre múltiples núcleos del procesador ($P \in \{1, 2, 4, 8\}$).
2. **Resolver dependencias espaciales** entre subdominios mediante el intercambio síncrono de fronteras (*halo exchange*) sin compartir memoria directa ni provocar condiciones de carrera.
3. **Evaluar empíricamente el rendimiento paralelo** midiendo tiempos de ejecución, aceleración (*Speedup*), eficiencia y los límites impuestos por la sobrecarga de comunicación (Ley de Amdahl).

## Arquitectura del Código (Metodología PCAM)

El algoritmo resuelve la ecuación de difusión en 2D mediante el método iterativo de Jacobi (*stencil* de 5 puntos) estructurado en cuatro fases:

### 1. Fase 1: Particionamiento (`inicializacion_subdominio`)
* Segmenta el dominio global de $N \times N$ ($500 \times 500$) en $P$ franjas horizontales de tamaño $(N/P) \times N$.
* Añade **2 filas adicionales (*Ghost Cells*)** en los extremos superior (`índice 0`) e inferior (`índice subgrid_rows + 1`) de cada matriz local para almacenar las lecturas de los procesos vecinos.
* Inicializa una perturbación Gaussiana/exponencial centrada en las coordenadas $(50, 50)$.

### 2. Fase 2: Comunicación (`intercambio_ghost_cells`)
* Antes de calcular el paso de tiempo $t+1$, cada proceso se comunica con sus vecinos del Norte y del Sur a través de tuberías bidireccionales (`Pipe`).
* Envía sus filas límite reales (`fila 1` y `fila subgrid_rows`) y recibe las fronteras vecinas en sus filas fantasma.
* Utiliza alternancia por paridad (`rank % 2`) para evitar interbloqueos (*deadlocks*) en el búfer del sistema operativo.

### 3. Fase 3: Agrupamiento y Cómputo (`calcular_paso_atmosferico`)
* Actualiza el estado físico de cada celda promediando sus 4 vecinos inmediatos (Norte, Sur, Este y Oeste):
  $$U_{i,j}^{t+1} = 0.25 \times \left( U_{i-1,j}^t + U_{i+1,j}^t + U_{i,j-1}^t + U_{i,j+1}^t \right)$$
* Emplea operaciones vectorizadas con **NumPy** para maximizar el uso de la memoria caché del procesador.

### 4. Fase 4: Integración (`worker_spmd` y `ejecutar_simulacion`)
* Orquesta a los $P$ procesos trabajadores a lo largo de $200$ iteraciones temporales, recolecta muestras periódicas del fenómeno y mide el tiempo total de ejecución.

**Salida en consola:**
```text
Simulacion iniciada en Windows (N=500, pasos=200)...

Procesos (P)    | Tiempo T(P) [s]    | Speedup S(P)    | Eficiencia E(P)
----------------------------------------------------------------------
1               | 0.5840             | 1.00            | 100.0         %
2               | 0.4964             | 1.18            | 58.8          %
4               | 0.3451             | 1.69            | 42.3          %
8               | 0.3780             | 1.54            | 19.3          %
