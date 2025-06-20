#!/usr/bin/env python3
"""Benchmark specific Pasta operations.

This script measures the performance of key operations like:
- Clipboard read/write
- History storage operations
- Settings load/save
- Typing simulation
"""

import random
import statistics
import string
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def generate_test_data(size: int) -> str:
    """Generate random text of specified size."""
    return "".join(random.choices(string.ascii_letters + string.digits + " \n", k=size))


def benchmark_clipboard_operations(num_iterations: int = 100) -> dict[str, float]:
    """Benchmark clipboard read/write operations."""
    import pyperclip

    results: dict[str, float] = {}

    # Test data of various sizes
    test_sizes = [10, 100, 1000, 10000]

    print("Benchmarking clipboard operations...")

    for size in test_sizes:
        test_data = generate_test_data(size)

        # Benchmark writes
        write_times = []
        for _ in range(num_iterations):
            start = time.perf_counter()
            pyperclip.copy(test_data)
            write_times.append(time.perf_counter() - start)

        # Benchmark reads
        read_times = []
        for _ in range(num_iterations):
            start = time.perf_counter()
            _ = pyperclip.paste()
            read_times.append(time.perf_counter() - start)

        results[f"write_{size}"] = statistics.mean(write_times)
        results[f"read_{size}"] = statistics.mean(read_times)

    # Test change detection using just clipboard operations
    detection_times = []
    for i in range(20):
        test_text = f"Test {i}"
        start = time.perf_counter()
        pyperclip.copy(test_text)
        # Just measure the copy time as a proxy for change detection
        detection_times.append(time.perf_counter() - start)
        time.sleep(0.01)  # Small delay between tests

    results["change_detection"] = statistics.mean(detection_times)

    return results


def benchmark_storage_operations(num_iterations: int = 100) -> dict[str, float]:
    """Benchmark storage operations."""
    from pasta.core.storage import StorageManager

    results: dict[str, float] = {}

    print("Benchmarking storage operations...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        storage = StorageManager(db_path)

        # Test data
        test_entries = [
            {"content": generate_test_data(100), "timestamp": time.time(), "content_type": "text", "hash": f"hash{i}"}
            for i in range(num_iterations)
        ]

        # Benchmark inserts
        insert_times = []
        for entry in test_entries:
            start = time.perf_counter()
            storage.save_entry(entry)
            insert_times.append(time.perf_counter() - start)

        results["insert_mean"] = statistics.mean(insert_times)
        results["insert_median"] = statistics.median(insert_times)

        # Benchmark queries
        query_times = []
        for _ in range(20):
            start = time.perf_counter()
            _ = storage.get_history(limit=50)
            query_times.append(time.perf_counter() - start)

        results["query_50_mean"] = statistics.mean(query_times)

        # Benchmark search
        search_times = []
        search_terms = ["test", "data", "content", "abc"]
        for term in search_terms:
            start = time.perf_counter()
            _ = storage.search_entries(term)
            search_times.append(time.perf_counter() - start)

        results["search_mean"] = statistics.mean(search_times)

        # Benchmark delete
        delete_times = []
        entries = storage.get_history(limit=10)
        for entry in entries[:5]:
            start = time.perf_counter()
            entry_id = entry["id"]
            assert isinstance(entry_id, int)
            storage.delete_entry(entry_id)
            delete_times.append(time.perf_counter() - start)

        if delete_times:
            results["delete_mean"] = statistics.mean(delete_times)

    finally:
        Path(db_path).unlink(missing_ok=True)

    return results


def benchmark_settings_operations(num_iterations: int = 50) -> dict[str, float]:
    """Benchmark settings load/save operations."""
    from pasta.core.settings import SettingsManager

    results: dict[str, float] = {}

    print("Benchmarking settings operations...")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        settings_path = tmp.name

    try:
        manager = SettingsManager(settings_path=Path(settings_path))

        # Benchmark loads
        load_times = []
        for _ in range(num_iterations):
            start = time.perf_counter()
            manager.load()
            load_times.append(time.perf_counter() - start)

        results["load_mean"] = statistics.mean(load_times)
        results["load_median"] = statistics.median(load_times)

        # Benchmark saves
        save_times = []
        for i in range(num_iterations):
            # Modify a setting
            manager.settings.typing_speed = 100 + i

            start = time.perf_counter()
            manager.save()
            save_times.append(time.perf_counter() - start)

        results["save_mean"] = statistics.mean(save_times)
        results["save_median"] = statistics.median(save_times)

        # Benchmark observer notifications
        notification_times = []

        def dummy_observer(settings: Any) -> None:  # noqa: ARG001
            pass

        manager.add_observer(dummy_observer)

        for i in range(20):
            start = time.perf_counter()
            manager.settings.typing_speed = 200 + i
            manager._notify_observers()
            notification_times.append(time.perf_counter() - start)

        results["notify_mean"] = statistics.mean(notification_times)

    finally:
        Path(settings_path).unlink(missing_ok=True)

    return results


def benchmark_typing_simulation(num_iterations: int = 10) -> dict[str, float]:  # noqa: ARG001
    """Benchmark keyboard typing simulation."""
    from pasta.core.keyboard import PastaKeyboardEngine

    results: dict[str, float] = {}

    print("Benchmarking typing simulation...")

    engine = PastaKeyboardEngine()

    # Test different text sizes
    test_sizes = [10, 50, 100, 500]

    for size in test_sizes:
        test_text = generate_test_data(size)

        # Measure chunking time
        start = time.perf_counter()
        # Simulate chunking by splitting text
        chunk_size = 200
        _ = [test_text[i : i + chunk_size] for i in range(0, len(test_text), chunk_size)]
        results[f"chunk_{size}"] = time.perf_counter() - start

        # Measure delay calculation
        delay_times = []
        for _ in range(100):
            start = time.perf_counter()
            # Use get_adaptive_engine to calculate typing delay
            adaptive = engine.get_adaptive_engine()
            _ = adaptive.get_typing_interval()
            delay_times.append(time.perf_counter() - start)

        results[f"delay_calc_{size}"] = statistics.mean(delay_times)

    # Test adaptive delay under different CPU loads
    # Note: We can't actually simulate typing without side effects,
    # so we just test the delay calculation logic

    return results


def print_benchmark_results(all_results: dict[str, dict[str, float]]) -> None:
    """Pretty print benchmark results."""
    print("\n" + "=" * 60)
    print("PASTA OPERATION BENCHMARKS")
    print("=" * 60)

    # Clipboard results
    if "clipboard" in all_results:
        print("\n📋 Clipboard Operations:")
        results = all_results["clipboard"]

        print("\n  Write Operations (avg ms):")
        for size in [10, 100, 1000, 10000]:
            if f"write_{size}" in results:
                print(f"    {size:5d} chars: {results[f'write_{size}'] * 1000:.3f} ms")

        print("\n  Read Operations (avg ms):")
        for size in [10, 100, 1000, 10000]:
            if f"read_{size}" in results:
                print(f"    {size:5d} chars: {results[f'read_{size}'] * 1000:.3f} ms")

        if "change_detection" in results:
            print(f"\n  Change Detection: {results['change_detection'] * 1000:.3f} ms")

    # Storage results
    if "storage" in all_results:
        print("\n💾 Storage Operations:")
        results = all_results["storage"]

        print(f"  Insert (mean):     {results.get('insert_mean', 0) * 1000:.3f} ms")
        print(f"  Insert (median):   {results.get('insert_median', 0) * 1000:.3f} ms")
        print(f"  Query 50 items:    {results.get('query_50_mean', 0) * 1000:.3f} ms")
        print(f"  Search:            {results.get('search_mean', 0) * 1000:.3f} ms")
        if "delete_mean" in results:
            print(f"  Delete:            {results['delete_mean'] * 1000:.3f} ms")

    # Settings results
    if "settings" in all_results:
        print("\n⚙️  Settings Operations:")
        results = all_results["settings"]

        print(f"  Load (mean):       {results.get('load_mean', 0) * 1000:.3f} ms")
        print(f"  Load (median):     {results.get('load_median', 0) * 1000:.3f} ms")
        print(f"  Save (mean):       {results.get('save_mean', 0) * 1000:.3f} ms")
        print(f"  Save (median):     {results.get('save_median', 0) * 1000:.3f} ms")
        print(f"  Notify observers:  {results.get('notify_mean', 0) * 1000:.3f} ms")

    # Typing results
    if "typing" in all_results:
        print("\n⌨️  Typing Simulation:")
        results = all_results["typing"]

        print("\n  Text Chunking (ms):")
        for size in [10, 50, 100, 500]:
            if f"chunk_{size}" in results:
                print(f"    {size:3d} chars: {results[f'chunk_{size}'] * 1000:.3f} ms")

        print("\n  Delay Calculation (avg μs):")
        for size in [10, 50, 100, 500]:
            if f"delay_calc_{size}" in results:
                print(f"    {size:3d} chars: {results[f'delay_calc_{size}'] * 1000000:.1f} μs")

    print("\n" + "=" * 60)


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Pasta operations")
    parser.add_argument("--clipboard", action="store_true", help="Run clipboard benchmarks")
    parser.add_argument("--storage", action="store_true", help="Run storage benchmarks")
    parser.add_argument("--settings", action="store_true", help="Run settings benchmarks")
    parser.add_argument("--typing", action="store_true", help="Run typing simulation benchmarks")
    parser.add_argument("--all", action="store_true", help="Run all benchmarks")
    parser.add_argument("-n", "--iterations", type=int, default=100, help="Number of iterations for benchmarks")

    args = parser.parse_args()

    # Default to all if nothing specified
    if not any([args.clipboard, args.storage, args.settings, args.typing, args.all]):
        args.all = True

    all_results: dict[str, dict[str, float]] = {}

    try:
        if args.all or args.clipboard:
            all_results["clipboard"] = benchmark_clipboard_operations(args.iterations)

        if args.all or args.storage:
            all_results["storage"] = benchmark_storage_operations(args.iterations)

        if args.all or args.settings:
            all_results["settings"] = benchmark_settings_operations(args.iterations)

        if args.all or args.typing:
            all_results["typing"] = benchmark_typing_simulation(min(args.iterations, 10))

        print_benchmark_results(all_results)

    except Exception as e:
        print(f"Error during benchmarking: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
