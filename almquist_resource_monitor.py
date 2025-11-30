#!/usr/bin/env python3
"""
ALMQUIST Resource Monitor
Monitors CPU, GPU, disk, and memory usage during crawling
"""

import psutil
import shutil
import subprocess
import sys
from datetime import datetime

class ResourceMonitor:
    """Monitor system resources and enforce limits"""

    def __init__(self,
                 cpu_limit=80,
                 disk_limit=90,
                 mem_limit=85,
                 gpu_limit=80):
        self.cpu_limit = cpu_limit
        self.disk_limit = disk_limit
        self.mem_limit = mem_limit
        self.gpu_limit = gpu_limit

    def check_cpu(self):
        """Check CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent >= self.cpu_limit:
            return False, cpu_percent
        return True, cpu_percent

    def check_disk(self):
        """Check disk usage"""
        disk = shutil.disk_usage("/")
        percent_used = (disk.used / disk.total) * 100

        if percent_used >= self.disk_limit:
            return False, percent_used, disk.free / (1024**3)
        return True, percent_used, disk.free / (1024**3)

    def check_memory(self):
        """Check memory usage"""
        mem = psutil.virtual_memory()
        if mem.percent >= self.mem_limit:
            return False, mem.percent
        return True, mem.percent

    def check_gpu(self):
        """Check GPU usage (NVIDIA)"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                gpu_data = []

                for line in lines:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        gpu_util = float(parts[0].strip())
                        mem_used = float(parts[1].strip())
                        mem_total = float(parts[2].strip())
                        mem_percent = (mem_used / mem_total) * 100

                        gpu_data.append({
                            'utilization': gpu_util,
                            'memory_percent': mem_percent
                        })

                        if gpu_util >= self.gpu_limit or mem_percent >= self.gpu_limit:
                            return False, gpu_data

                return True, gpu_data
            else:
                return True, None  # No GPU or nvidia-smi not available

        except Exception as e:
            return True, None  # GPU check failed, continue

    def check_all(self, verbose=True):
        """Check all resources"""
        issues = []

        # CPU
        cpu_ok, cpu_percent = self.check_cpu()
        if not cpu_ok:
            issues.append(f"CPU: {cpu_percent:.1f}% (limit: {self.cpu_limit}%)")
        elif verbose:
            print(f"   CPU: {cpu_percent:.1f}%")

        # Memory
        mem_ok, mem_percent = self.check_memory()
        if not mem_ok:
            issues.append(f"Memory: {mem_percent:.1f}% (limit: {self.mem_limit}%)")
        elif verbose:
            print(f"   Memory: {mem_percent:.1f}%")

        # Disk
        disk_ok, disk_percent, disk_free = self.check_disk()
        if not disk_ok:
            issues.append(f"Disk: {disk_percent:.1f}% used, {disk_free:.1f} GB free (limit: {self.disk_limit}%)")
        elif verbose:
            print(f"   Disk: {disk_percent:.1f}% used, {disk_free:.1f} GB free")

        # GPU
        gpu_ok, gpu_data = self.check_gpu()
        if not gpu_ok and gpu_data:
            for i, gpu in enumerate(gpu_data):
                issues.append(f"GPU{i}: {gpu['utilization']:.1f}% util, {gpu['memory_percent']:.1f}% mem (limit: {self.gpu_limit}%)")
        elif verbose and gpu_data:
            for i, gpu in enumerate(gpu_data):
                print(f"   GPU{i}: {gpu['utilization']:.1f}% util, {gpu['memory_percent']:.1f}% mem")

        if issues:
            print(f"\n⚠️  RESOURCE LIMIT EXCEEDED:")
            for issue in issues:
                print(f"   {issue}")
            return False

        return True

    def print_status(self):
        """Print current resource status"""
        print(f"\n📊 Resource Status ({datetime.now().strftime('%H:%M:%S')})")
        print(f"{'─'*50}")
        self.check_all(verbose=True)
        print(f"{'─'*50}")


if __name__ == "__main__":
    monitor = ResourceMonitor()
    monitor.print_status()
