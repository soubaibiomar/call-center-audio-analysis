#requires -Version 7.2
[CmdletBinding()]
param(
    [string]$OutputPath = 'docs/environment/evidence/step01-environment.json',
    [string]$GpuImage = 'nvidia/cuda:12.9.0-base-ubuntu22.04',
    [switch]$LibraryOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Protect-UserPaths {
    param([AllowEmptyString()][string]$Value)
    foreach ($privateRoot in @($env:USERPROFILE, $HOME) | Select-Object -Unique) {
        if ($privateRoot) {
            $Value = $Value.Replace($privateRoot, '<USERPROFILE>', [StringComparison]::OrdinalIgnoreCase)
            $Value = $Value.Replace($privateRoot.Replace('\', '/'), '<USERPROFILE>', [StringComparison]::OrdinalIgnoreCase)
        }
    }
    return $Value
}

function Invoke-ToolCheck {
    param(
        [Parameter(Mandatory)][string]$Executable,
        [string[]]$Arguments = @(),
        [ValidateRange(1, 120)][int]$TimeoutSeconds = 20
    )
    $record = [ordered]@{
        executable = Protect-UserPaths $Executable
        arguments = @($Arguments | ForEach-Object { Protect-UserPaths $_ }); path = $null
        status = 'MISSING'; exit_code = $null; stdout = ''; stderr = ''; elapsed_ms = 0
        output_capture_complete = $null
    }
    $found = Get-Command $Executable -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $found) { return [pscustomobject]$record }
    $record.path = Protect-UserPaths $found.Source
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $found.Source
    $start.UseShellExecute = $false
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($argument in $Arguments) { $start.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $start
    $watch = [Diagnostics.Stopwatch]::StartNew()
    try {
        $null = $process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            $process.Kill($true)
            $null = $process.WaitForExit(2000)
            $record.status = 'TIMEOUT'
        } else {
            $record.exit_code = $process.ExitCode
            $record.status = if ($process.ExitCode -eq 0) { 'PASS' } else { 'FAILED' }
        }
        # Descendants can retain pipe handles after the direct child exits.
        $remaining = [Math]::Max(0, $TimeoutSeconds * 1000 - [int]$watch.ElapsedMilliseconds)
        $record.output_capture_complete = [Threading.Tasks.Task]::WaitAll(
            [Threading.Tasks.Task[]]@($stdout, $stderr), $remaining
        )
        if ($stdout.IsCompletedSuccessfully) {
            $record.stdout = Protect-UserPaths ($stdout.GetAwaiter().GetResult().TrimEnd())
        }
        if ($stderr.IsCompletedSuccessfully) {
            $record.stderr = Protect-UserPaths ($stderr.GetAwaiter().GetResult().TrimEnd())
        }
        if (-not $record.output_capture_complete) {
            $record.status = 'TIMEOUT'
            $record.exit_code = $null
            $record.stderr = ($record.stderr + "`nOutput capture exceeded the command deadline.").Trim()
        }
    } catch {
        $record.status = 'ERROR'
        $record.stderr = Protect-UserPaths $_.Exception.Message
    } finally {
        $watch.Stop()
        $record.elapsed_ms = $watch.ElapsedMilliseconds
        $process.Dispose()
    }
    return [pscustomobject]$record
}

function Get-ServiceSnapshot {
    $ids = Invoke-ToolCheck docker @('ps', '-aq', '--no-trunc')
    if ($ids.status -ne 'PASS') { return $ids }
    $format = '{{.Id}}|{{.Name}}|{{.Config.Image}}|{{.State.Status}}|{{.State.StartedAt}}|{{.RestartCount}}'
    $snapshot = if ($ids.stdout) {
        Invoke-ToolCheck docker (@('inspect', '--format', $format) + @($ids.stdout -split '\r?\n'))
    } else { $ids }
    if ($snapshot.status -eq 'PASS') {
        $rows = @($snapshot.stdout -split '\r?\n' | Where-Object { $_ })
        $running = @($rows | Where-Object { ($_ -split '\|')[3] -eq 'running' })
        $ollama = @($rows | Where-Object { ($_ -split '\|')[1, 2] -match 'ollama' })
        $snapshot | Add-Member -NotePropertyName container_count -NotePropertyValue $rows.Count
        $snapshot | Add-Member -NotePropertyName running_count -NotePropertyValue $running.Count
        $snapshot | Add-Member -NotePropertyName ollama_count -NotePropertyValue $ollama.Count
        # Retain evidence of identity/state without publishing unrelated project names.
        $snapshot.stdout = ($rows | ForEach-Object {
            [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($_)))
        }) -join "`n"
    }
    return $snapshot
}

function Test-ServiceContinuity {
    param([Parameter(Mandatory)]$Before, [Parameter(Mandatory)]$After)
    if ($Before.status -ne 'PASS' -or $After.status -ne 'PASS') {
        return [pscustomobject]@{ status = 'UNVERIFIED'; reason = 'A service snapshot failed.' }
    }
    $first = @($Before.stdout -split '\r?\n' | Where-Object { $_ } | Sort-Object)
    $last = @($After.stdout -split '\r?\n' | Where-Object { $_ } | Sort-Object)
    $changed = @((Compare-Object $first $last))
    return [pscustomobject]@{
        status = if ($changed.Count -eq 0) { 'PASS' } else { 'CHANGED' }
        reason = 'Compared container ID, name, image, state, start time and restart count; point-in-time evidence only.'
    }
}

if ($LibraryOnly) { return }

$tools = [ordered]@{}
foreach ($name in @('git', 'python', 'uv', 'docker', 'node', 'ffmpeg', 'code')) {
    $flag = if ($name -eq 'ffmpeg') { '-version' } else { '--version' }
    $tools[$name] = Invoke-ToolCheck $name @($flag)
}
$tools['docker_compose'] = Invoke-ToolCheck docker @('compose', 'version')
# npm.cmd is a batch shim: execute its JavaScript entry with Node, without a shell.
$npm = Get-Command npm.cmd -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if ($npm) {
    $npmCli = Join-Path (Split-Path $npm.Source) 'node_modules/npm/bin/npm-cli.js'
    $tools['npm'] = Invoke-ToolCheck node @($npmCli, '--version')
    $tools['npm'] | Add-Member -NotePropertyName launcher_path -NotePropertyValue (Protect-UserPaths $npm.Source)
} else {
    $tools['npm'] = Invoke-ToolCheck npm.cmd @('--version')
}
$gpuQuery = @('--query-gpu=name,memory.total,memory.used,driver_version', '--format=csv,noheader,nounits')
$tools['nvidia_smi'] = Invoke-ToolCheck nvidia-smi $gpuQuery
$before = Get-ServiceSnapshot
$dockerInfo = Invoke-ToolCheck docker @('info', '--format', '{{.OSType}}|{{.Architecture}}|{{.ServerVersion}}|{{range $name, $runtime := .Runtimes}}{{$name}},{{end}}|{{.DefaultRuntime}}')
$dockerContext = Invoke-ToolCheck docker @('context', 'show')
$image = Invoke-ToolCheck docker @('image', 'inspect', $GpuImage, '--format', '{{.Id}}')
$probeName = 'project28-gpu-probe-' + [guid]::NewGuid().ToString('N')
$gpuProbe = [pscustomobject]@{ status = 'NOT_EXECUTED'; reason = 'GPU image unavailable locally; automatic pulls forbidden.' }
if ($dockerInfo.status -eq 'PASS' -and $image.status -eq 'PASS') {
    try {
        $gpuProbe = Invoke-ToolCheck docker (@('run', '--rm', '--name', $probeName, '--pull=never', '--network=none', '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--gpus', 'all', $GpuImage, 'nvidia-smi') + $gpuQuery) 60
    } finally {
        # Cleanup only the uniquely named probe if --rm did not already remove it.
        $leftover = Invoke-ToolCheck docker @('ps', '-aq', '--filter', "name=^/$probeName`$")
        if ($leftover.status -eq 'PASS' -and $leftover.stdout) {
            $null = Invoke-ToolCheck docker @('rm', '-f', $probeName)
        }
    }
}
$after = Get-ServiceSnapshot
$gpuAfter = Invoke-ToolCheck nvidia-smi $gpuQuery

$resources = [ordered]@{}
try {
    $osInfo = Get-CimInstance Win32_OperatingSystem
    $resources['os'] = [ordered]@{
        caption = $osInfo.Caption; version = $osInfo.Version; build = $osInfo.BuildNumber
        total_ram_bytes = [long]$osInfo.TotalVisibleMemorySize * 1024
        available_ram_bytes = [long]$osInfo.FreePhysicalMemory * 1024
    }
    $resources['disks'] = @(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
        [ordered]@{ drive = $_.DeviceID; size_bytes = [long]$_.Size; free_bytes = [long]$_.FreeSpace }
    })
} catch { $resources['error'] = Protect-UserPaths $_.Exception.Message }
try {
    $resources['listeners'] = @(Get-NetTCPConnection -State Listen | Sort-Object LocalPort, OwningProcess | ForEach-Object {
        [ordered]@{ port = $_.LocalPort; pid = $_.OwningProcess; address_scope = if ($_.LocalAddress -in @('127.0.0.1', '::1')) { 'loopback' } elseif ($_.LocalAddress -in @('0.0.0.0', '::')) { 'wildcard' } else { 'specific-address-redacted' } }
    })
} catch { $resources['listener_error'] = Protect-UserPaths $_.Exception.Message }

$report = [ordered]@{
    schema_version = 1; captured_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
    powershell_version = $PSVersionTable.PSVersion.ToString()
    working_revision = Invoke-ToolCheck git @('rev-parse', 'HEAD')
    upstream_revision = Invoke-ToolCheck git @('rev-parse', 'upstream/main')
    branch = Invoke-ToolCheck git @('branch', '--show-current')
    path = @($env:PATH -split ';' | ForEach-Object { Protect-UserPaths $_ })
    tools = $tools; docker_info = $dockerInfo; docker_context = $dockerContext
    gpu_image = $image; container_gpu = $gpuProbe
    services_before = $before; services_after = $after
    service_continuity = Test-ServiceContinuity $before $after
    gpu_after = $gpuAfter; resources = $resources
    limitations = @('No model inference or training; VRAM observations are not inference peak memory.', 'No secrets, container environment, audio or model volume contents inspected.')
}
$destination = [IO.Path]::GetFullPath($OutputPath)
$null = New-Item -ItemType Directory -Force -Path (Split-Path $destination)
[IO.File]::WriteAllText($destination, ($report | ConvertTo-Json -Depth 10) + "`n", [Text.UTF8Encoding]::new($false))
Write-Output "Environment evidence saved to $(Protect-UserPaths $destination)"
