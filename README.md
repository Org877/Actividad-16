# Actividad-16
# 202216
# Omar Reyes Gonzalez
##  Propósito del Proyecto

En la computación de alto rendimiento (HPC) y la predicción meteorológica moderna, modelar fenómenos físicos sobre grandes regiones geográficas requiere millones de cálculos por segundo. Este proyecto implementa la técnica de **Descomposición de Dominio con Celdas Fantasma (*Ghost Cells*)** para:

1. **Dividir la carga computacional** de una malla espacial entre múltiples núcleos del procesador ($P \in \{1, 2, 4, 8\}$).
2. **Resolver dependencias espaciales** entre subdominios mediante el intercambio síncrono de fronteras (*halo exchange*) sin compartir memoria directa ni provocar condiciones de carrera.
3. **Evaluar empíricamente el rendimiento paralelo** midiendo tiempos de ejecución, aceleración (*Speedup*), eficiencia y los límites impuestos por la sobrecarga de comunicación (Ley de Amdahl).
