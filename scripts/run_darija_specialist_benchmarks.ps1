param([switch]$WaitForDownloads)
$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path '.').Path
$cache = (Resolve-Path "$env:USERPROFILE/.cache/huggingface/hub").Path
$root = Join-Path $workspace '.local/darija-specialist-20261029'
$evidence = Join-Path $workspace 'docs/benchmarks/evidence/darija-specialist-20261029'
$manifest = '.local/darija-specialist-20261029/manifest.json'
$manifestHash = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()
$modelReceipt = Join-Path $workspace '.local/model-upgrade-20261029/moulsot/download-receipt.json'
$deadline = (Get-Date).AddMinutes(45)
while (-not (Test-Path -LiteralPath $modelReceipt)) {
    if (-not $WaitForDownloads) { throw 'MoulSot download is not verified' }
    $active = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'download_upgrade_models.py.*moulsot' })
    if ($active.Count -eq 0 -or (Get-Date) -gt $deadline) { throw 'Model download stopped or exceeded wait limit; preserve partial files' }
    Start-Sleep -Seconds 3
}
if (-not (Test-Path -LiteralPath (Join-Path $root 'darija-small-ct2/conversion-receipt.json'))) { throw 'Whisper conversion is not complete' }
foreach ($name in @('darija-small','moulsot')) {
    Copy-Item -LiteralPath (Join-Path $workspace ".local/model-upgrade-20261029/$name/download-receipt.json") -Destination (Join-Path $evidence "$name-download.json")
}
$jobs = @(
    @('small-base','whisper','/models/models--Systran--faster-whisper-small/snapshots/536b0662742c02347bc0e980a01041f333bce120','project28-upgrade-whisper:local'),
    @('small-darija','whisper','/workspace/.local/darija-specialist-20261029/darija-small-ct2','project28-upgrade-whisper:local'),
    @('turbo-base','whisper','/workspace/.local/model-upgrade-20261029/turbo','project28-upgrade-whisper:local'),
    @('qwen-base','qwen','/workspace/.local/model-upgrade-20261029/qwen17','project28-step13-qwen:headers'),
    @('moulsot','qwen','/workspace/.local/model-upgrade-20261029/moulsot','project28-step13-qwen:headers')
)
$wasRunning = (& docker inspect ollama --format '{{.State.Running}}') -eq 'true'
$stopped = $false
$receipts = @()
try {
    if ($wasRunning) {
        & docker stop --timeout 20 ollama
        if ($LASTEXITCODE -ne 0) { throw 'Could not release Ollama GPU memory' }
        $stopped = $true
    }
    foreach ($job in $jobs) {
        $output = "docs/benchmarks/evidence/darija-specialist-20261029/$($job[0]).json"
        if (Test-Path -LiteralPath $output) {
            $existing = Get-Content -LiteralPath $output -Raw | ConvertFrom-Json
            if ($existing.manifest_sha256 -eq $manifestHash -and $existing.observations.Count -eq 100) {
                Write-Output "$($job[0]) already complete on this frozen sample"
                continue
            }
            throw "Preserve partial or mismatched output: $output"
        }
        $started = (Get-Date).ToUniversalTime().ToString('o')
        $arguments = @('run','--rm','--gpus','all','--network','none','--entrypoint','python',
            '-v',"${workspace}:/workspace",'-v',"${cache}:/models:ro",'-w','/workspace',
            $job[3],'-u','scripts/benchmark_upgrade_asr.py','--backend',$job[1],
            '--model',$job[2],'--device','cuda','--repetitions','1','--output',$output,
            '--manifest',$manifest,'--manifest-sha256',$manifestHash,'--languages','ary',
            '--qwen-dtype','bfloat16','--private-predictions',
            ".local/darija-specialist-20261029/$($job[0])-predictions.jsonl",'--whisper-greedy')
        & docker @arguments *> (Join-Path $root "$($job[0]).log")
        $code = $LASTEXITCODE
        $receipts += @{model=$job[0]; arguments=$arguments; exit_code=$code; started_utc=$started;
            finished_utc=(Get-Date).ToUniversalTime().ToString('o')}
        $receipts | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $evidence 'execution.json')
        Write-Output "$($job[0]) exit $code"
    }
}
finally {
    if ($stopped) { & docker start ollama; Write-Output 'Ollama restarted' }
}
if (@($receipts | Where-Object {$_.exit_code -ne 0}).Count -gt 0) { exit 1 }
