import time
from contextlib import contextmanager
from collections import defaultdict
import click

class Profiler:
    """Simple profiler for tracking timing of operations."""
    
    def __init__(self, enabled=False):
        self.enabled = enabled
        self.timings = defaultdict(list)
        self.current_step = None
        self.step_start = None
    
    @contextmanager
    def step(self, name):
        """Context manager for timing a step."""
        if not self.enabled:
            yield
            return
        
        start_time = time.time()
        self.current_step = name
        self.step_start = start_time
        
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            self.timings[name].append(duration)
            
            if self.enabled:
                click.echo(f"⏱️  {name}: {duration:.2f}s", err=True)
            
            self.current_step = None
            self.step_start = None
    
    def log(self, message):
        """Log a message with timing info if profiling is enabled."""
        if not self.enabled:
            return
        
        current_time = time.time()
        if self.current_step and self.step_start:
            elapsed = current_time - self.step_start
            click.echo(f"⏱️    └─ {message} (+{elapsed:.2f}s)", err=True)
        else:
            click.echo(f"⏱️  {message}", err=True)
    
    def print_summary(self):
        """Print a summary of all timings."""
        if not self.enabled or not self.timings:
            return
        
        click.echo("\n" + "="*50, err=True)
        click.echo("⏱️  PROFILING SUMMARY", err=True)
        click.echo("="*50, err=True)
        
        total_time = 0
        for step_name, times in self.timings.items():
            step_total = sum(times)
            step_avg = step_total / len(times)
            step_count = len(times)
            
            total_time += step_total
            
            if step_count > 1:
                click.echo(f"{step_name:30s}: {step_total:8.2f}s total ({step_count}x, avg: {step_avg:.2f}s)", err=True)
            else:
                click.echo(f"{step_name:30s}: {step_total:8.2f}s", err=True)
        
        click.echo("-" * 50, err=True)
        click.echo(f"{'TOTAL':30s}: {total_time:8.2f}s", err=True)
        click.echo("="*50 + "\n", err=True)

# Global profiler instance
profiler = Profiler()

def enable_profiling():
    """Enable profiling globally."""
    global profiler
    profiler.enabled = True

def disable_profiling():
    """Disable profiling globally."""
    global profiler
    profiler.enabled = False