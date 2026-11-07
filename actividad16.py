#Omar reyes 
#202216

import os
# 1. Evitar que NumPy/OpenBLAS colapse Windows al lanzar múltiples procesos
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import time
import numpy as np
from multiprocessing import Process, Pipe, freeze_support

#  Particionamiento
def inicializacion_subdominio(rank, n_proc, N, pert=1.01):
    subgrid_rows = N // n_proc
    cols = N
    grid = np.zeros((subgrid_rows + 2, cols + 2), dtype=np.float64)

    # Inicialización vectorizada 
    global_row_start = rank * subgrid_rows * pert
    r_idx = global_row_start + np.arange(subgrid_rows)[:, None]
    c_idx = np.arange(1, cols + 1)[None, :]
    dist = np.sqrt((r_idx - 50.0)**2 + (c_idx - 50.0)**2)
    grid[1:subgrid_rows + 1, 1:cols + 1] = 100.0 * np.exp(-dist / 120.0)

    return grid, subgrid_rows, cols

#  Comunicación 
def intercambio_ghost_cells(rank, grid, subgrid_rows, pipe_top, pipe_bottom):
    # Alternar el orden send y recv según si el proceso es par o impar para evitar bloqueo
    if rank % 2 == 0:
        if pipe_top is not None:
            pipe_top.send(grid[1, :].copy())
            grid[0, :] = pipe_top.recv()
        if pipe_bottom is not None:
            pipe_bottom.send(grid[subgrid_rows, :].copy())
            grid[subgrid_rows + 1, :] = pipe_bottom.recv()
    else:
        if pipe_bottom is not None:
            grid[subgrid_rows + 1, :] = pipe_bottom.recv()
            pipe_bottom.send(grid[subgrid_rows, :].copy())
        if pipe_top is not None:
            grid[0, :] = pipe_top.recv()
            pipe_top.send(grid[1, :].copy())

    # Condiciones de frontera laterales
    grid[:, 0] = grid[:, 1]
    grid[:, -1] = grid[:, -2]

#  Agrupamiento y replicación
def calcular_paso_atmosferico(grid, subgrid_rows, cols):
    grid_next = grid.copy()
    grid_next[1:subgrid_rows + 1, 1:cols + 1] = 0.25 * (
        grid[0:subgrid_rows, 1:cols + 1] +     # Vecino del Norte
        grid[2:subgrid_rows + 2, 1:cols + 1] + # Vecino del Sur
        grid[1:subgrid_rows + 1, 0:cols] +     # Vecino del Oeste
        grid[1:subgrid_rows + 1, 2:cols + 2]   # Vecino del Este
    )
    return grid_next

#  Integración 
def worker_spmd(rank, num_proc, N, steps, pipe_top, pipe_bottom, result_pipe, perturbacion):
    grid, subgrid_rows, cols = inicializacion_subdominio(rank, num_proc, N, perturbacion)
    historico = []
    sample_rate = steps // 10 if steps > 10 else 1

    for step in range(steps):
        intercambio_ghost_cells(rank, grid, subgrid_rows, pipe_top, pipe_bottom)
        grid = calcular_paso_atmosferico(grid, subgrid_rows, cols)
        if step % sample_rate == 0:
            historico.append((step, grid[1:subgrid_rows + 1, 1:cols + 1].copy()))

    # Enviar únicamente el número de muestras o el estado final si el Pipe de Windows satura el búfer,
    # o enviar el histórico completo vaciándolo desde el proceso padre antes de join()
    result_pipe.send(len(historico))
    result_pipe.close()

def ejecutar_simulacion(P, N=500, steps=200):
    neighbor_pipes = [Pipe() for _ in range(P - 1)]
    result_pipes = [Pipe(duplex=False) for _ in range(P)]
    procesos = []

    t_inicio = time.perf_counter()

    for rank in range(P):
        pipe_top = neighbor_pipes[rank - 1][1] if rank > 0 else None
        pipe_bottom = neighbor_pipes[rank][0] if rank < P - 1 else None
        recv_res, send_res = result_pipes[rank]

        p = Process(
            target=worker_spmd,
            args=(rank, P, N, steps, pipe_top, pipe_bottom, send_res, 1.01)
        )
        procesos.append((p, recv_res, send_res))
        p.start()
        # Cerrar la referencia de escritura en el padre
        send_res.close()

    # Leer resultados de cada proceso hijo
    resultados = [recv_res.recv() for _, recv_res, _ in procesos]

    for p, recv_res, _ in procesos:
        recv_res.close()
        p.join()

    return time.perf_counter() - t_inicio

if __name__ == "__main__":
    freeze_support()
    N_malla = 500
    pasos = 200
    procesadores = [1, 2, 4, 8]
    tiempos = {}

    print(f"\nSimulacion iniciada en Windows (N={N_malla}, pasos={pasos})...\n")
    print(f"{'Procesos (P)':<15} | {'Tiempo T(P) [s]':<18} | {'Speedup S(P)':<15} | {'Eficiencia E(P)':<15}")
    print("-" * 70)

    for P in procesadores:
        t_p = ejecutar_simulacion(P, N=N_malla, steps=pasos)
        tiempos[P] = t_p
        speedup = tiempos[1] / t_p
        eficiencia = (speedup / P) * 100
        print(f"{P:<15} | {t_p:<18.4f} | {speedup:<15.2f} | {eficiencia:<14.1f}%")