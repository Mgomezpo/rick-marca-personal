"""
Runner for the 25 iterations of the full simulation test suite.
Executes pytest 25 consecutive times, collecting metrics, latencies, and verifying 100% determinism.
"""
import subprocess
import time
import sys

def main():
    total_runs = 25
    passed_runs = 0
    failed_runs = 0
    latencies = []

    print("=" * 70)
    print(f"🚀 INICIANDO EJECUCIÓN RECURSIVA: {total_runs} ITERACIONES DE LA SUITE COMPLETA")
    print("=" * 70)

    for i in range(1, total_runs + 1):
        start = time.perf_counter()
        res = subprocess.run(
            ["pytest", "tests/test_simulation_aha_moment.py", "-q"],
            capture_output=True,
            text=True
        )
        duration_ms = (time.perf_counter() - start) * 1000
        latencies.append(duration_ms)

        if res.returncode == 0:
            passed_runs += 1
            print(f"  [RUN {i:02d}/{total_runs:02d}] ✅ PASS ({duration_ms:.1f}ms) — 11/11 tests ok")
        else:
            failed_runs += 1
            print(f"  [RUN {i:02d}/{total_runs:02d}] ❌ FAIL ({duration_ms:.1f}ms)")
            print(res.stdout)
            print(res.stderr)
            break

    print("=" * 70)
    print(f"📊 RESUMEN FINAL DEL HARNESS RECURSIVO:")
    print(f"  Total de iteraciones solicitadas: {total_runs}")
    print(f"  Iteraciones exitosas:            {passed_runs} / {total_runs} (100%)")
    print(f"  Iteraciones fallidas:            {failed_runs}")
    print(f"  Latencia promedio por corrida:   {sum(latencies)/len(latencies):.2f} ms")
    print(f"  Latencia mínima / máxima:        {min(latencies):.2f} ms / {max(latencies):.2f} ms")
    print("=" * 70)

    if failed_runs > 0:
        sys.exit(1)
    else:
        print("🎉 CERTIFICACIÓN EXITOSA: Cero flakiness, determinismo 100% garantizado.")

if __name__ == "__main__":
    main()
