#!/usr/bin/env python3
"""Measure Pasta application startup time."""

import sys
import time
from pathlib import Path
from statistics import mean, median, stdev


def measure_startup(iterations: int = 5, quick: bool = False) -> None:
    """Measure startup time across multiple iterations."""
    print(f"Measuring Pasta startup time over {iterations} iterations...")
    times = []

    for i in range(iterations):
        print(f"Iteration {i + 1}/{iterations}...")

        # Clear any cached imports
        modules_to_clear = [m for m in sys.modules if m.startswith("pasta")]
        for module in modules_to_clear:
            del sys.modules[module]

        # Measure import time
        import_start = time.perf_counter()
        from pasta.core.clipboard import ClipboardManager
        from pasta.core.keyboard import PastaKeyboardEngine
        from pasta.core.settings import SettingsManager
        from pasta.core.storage import StorageManager
        from pasta.utils.permissions import PermissionChecker

        import_time = time.perf_counter() - import_start

        # Measure component initialization
        init_start = time.perf_counter()

        # Initialize components
        permission_checker = PermissionChecker()
        clipboard_manager = ClipboardManager()
        keyboard_engine = PastaKeyboardEngine()

        # StorageManager needs a db_path
        import os

        if sys.platform == "darwin":
            data_dir = Path.home() / "Library" / "Application Support" / "Pasta"
        elif sys.platform == "win32":
            data_dir = Path(os.getenv("APPDATA", "")) / "Pasta"
        else:
            data_dir = Path.home() / ".local" / "share" / "pasta"

        data_dir.mkdir(parents=True, exist_ok=True)

        storage_manager = StorageManager(str(data_dir / "pasta.db"))
        settings_manager = SettingsManager()

        init_time = time.perf_counter() - init_start

        # Measure PySide6 import separately
        pyside_start = time.perf_counter()
        from pasta.gui.tray import SystemTray

        pyside_time = time.perf_counter() - pyside_start

        # Measure system tray setup (without running the event loop)
        tray_start = time.perf_counter()
        tray = SystemTray(
            clipboard_manager=clipboard_manager,
            keyboard_engine=keyboard_engine,
            storage_manager=storage_manager,
            permission_checker=permission_checker,
            settings_manager=settings_manager,
        )
        tray_time = time.perf_counter() - tray_start

        total_time = import_time + init_time + pyside_time + tray_time
        times.append({"import": import_time, "init": init_time, "pyside": pyside_time, "tray": tray_time, "total": total_time})

        # Clean up
        if hasattr(tray, "app") and tray.app:
            tray.app.quit()

        if quick:
            break

    # Print results
    print("\n" + "=" * 60)
    print("PASTA STARTUP TIME ANALYSIS")
    print("=" * 60)

    for phase in ["import", "init", "pyside", "tray", "total"]:
        phase_times = [t[phase] for t in times]
        print(f"\n{phase.upper()} PHASE:")
        print(f"  Mean:   {mean(phase_times) * 1000:.2f} ms")
        print(f"  Median: {median(phase_times) * 1000:.2f} ms")
        print(f"  Min:    {min(phase_times) * 1000:.2f} ms")
        print(f"  Max:    {max(phase_times) * 1000:.2f} ms")
        if len(phase_times) > 1:
            print(f"  StdDev: {stdev(phase_times) * 1000:.2f} ms")

    print("\n" + "=" * 60)
    print("BREAKDOWN BY COMPONENT (last iteration):")
    print("=" * 60)
    last = times[-1]
    print(f"Import phase:     {last['import'] * 1000:6.2f} ms ({last['import'] / last['total'] * 100:5.1f}%)")
    print(f"Init phase:       {last['init'] * 1000:6.2f} ms ({last['init'] / last['total'] * 100:5.1f}%)")
    print(f"PySide6 import:   {last['pyside'] * 1000:6.2f} ms ({last['pyside'] / last['total'] * 100:5.1f}%)")
    print(f"System tray:      {last['tray'] * 1000:6.2f} ms ({last['tray'] / last['total'] * 100:5.1f}%)")
    print(f"TOTAL:            {last['total'] * 1000:6.2f} ms")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Measure Pasta startup time")
    parser.add_argument("-n", "--iterations", type=int, default=5, help="Number of iterations")
    parser.add_argument("-q", "--quick", action="store_true", help="Quick mode (1 iteration)")
    args = parser.parse_args()

    measure_startup(args.iterations, args.quick)
