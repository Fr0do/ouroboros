import asyncio
import os
import socket


def _is_local(host: str) -> bool:
    names = {
        "localhost",
        "127.0.0.1",
        socket.gethostname(),
        socket.gethostname().split(".")[0],
    }
    extra = os.getenv("LOCAL_HOSTNAME", "")
    if extra:
        names.update(n.strip() for n in extra.split(","))
    return host in names


async def ssh_exec(host: str, command: str, timeout: int = 30) -> str:
    """Execute a command — locally if host is this machine, otherwise via SSH."""
    if _is_local(host):
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    else:
        proc = await asyncio.create_subprocess_exec(
            "ssh", host, command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return f"[TIMEOUT after {timeout}s]"

    out = stdout.decode().strip()
    err = stderr.decode().strip()
    if proc.returncode != 0 and err:
        return f"{out}\n[stderr] {err}" if out else f"[stderr] {err}"
    return out


async def ssh_tmux_send(host: str, session: str, command: str) -> str:
    """Send keys to a tmux session on remote host. Creates session if needed."""
    # Ensure session exists
    await ssh_exec(host, f"tmux has-session -t {session} 2>&1 || tmux new-session -d -s {session}")
    # Send command
    escaped = command.replace('"', '\\"')
    result = await ssh_exec(host, f'tmux send-keys -t {session} "{escaped}" Enter')
    return result or "OK"


async def ssh_tmux_capture(host: str, session: str, lines: int = 20) -> str:
    """Capture last N lines from a tmux pane."""
    return await ssh_exec(
        host,
        f"tmux capture-pane -t {session} -p | tail -{lines}",
        timeout=15,
    )


async def ssh_tmux_dump(host: str, session: str, history_lines: int = 5000,
                        save_path: str | None = None) -> str:
    """Capture full scrollback from tmux and optionally save to file on remote.

    Returns the captured text (may be large).
    """
    # -S -N captures N lines of scrollback history
    capture_cmd = f"tmux capture-pane -t {session} -p -S -{history_lines}"
    text = await ssh_exec(host, capture_cmd, timeout=30)

    if save_path and text.strip():
        # Save on remote for persistent access
        escaped_path = save_path.replace("'", "'\\''")
        await ssh_exec(
            host,
            f"mkdir -p $(dirname '{escaped_path}') && cat > '{escaped_path}' << 'CRASHLOG_EOF'\n{text}\nCRASHLOG_EOF",
            timeout=15,
        )

    return text


async def gpu_status(host: str) -> str:
    """Get compact GPU report: name, util, mem, temp, power, and top processes."""
    gpu_info = await ssh_exec(
        host,
        "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit --format=csv,noheader,nounits",
        timeout=10,
    )
    procs = await ssh_exec(
        host,
        "nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory,name --format=csv,noheader,nounits 2>/dev/null || echo ''",
        timeout=10,
    )
    # Map GPU UUIDs to indices for process listing
    uuid_map_raw = await ssh_exec(
        host,
        "nvidia-smi --query-gpu=index,uuid --format=csv,noheader",
        timeout=10,
    )
    uuid_to_idx = {}
    for line in uuid_map_raw.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 2:
            uuid_to_idx[parts[1]] = parts[0]

    lines = []
    for row in gpu_info.strip().splitlines():
        parts = [p.strip() for p in row.split(",")]
        if len(parts) < 8:
            lines.append(row)
            continue
        idx, name, util, mem_used, mem_total, temp, pwr, pwr_lim = parts
        # Shorten name (e.g. "NVIDIA A100-SXM4-80GB" -> "A100-80GB")
        short = name.replace("NVIDIA ", "").replace("-SXM4", "").replace("-SXM", "").replace("-PCIe", "")
        mem_pct = int(float(mem_used) / float(mem_total) * 100) if float(mem_total) > 0 else 0
        lines.append(f"[{idx}] {short}  {util}% | {mem_used}/{mem_total}MB ({mem_pct}%) | {temp}°C | {pwr}/{pwr_lim}W")

    if procs and procs.strip():
        lines.append("")
        for row in procs.strip().splitlines():
            parts = [p.strip() for p in row.split(",")]
            if len(parts) >= 4:
                uuid, pid, mem, cmd = parts[0], parts[1], parts[2], ",".join(parts[3:])
                idx = uuid_to_idx.get(uuid, "?")
                cmd_short = cmd.split("/")[-1][:30]
                lines.append(f"  gpu{idx} pid={pid} {mem}MB {cmd_short}")

    return "\n".join(lines)
