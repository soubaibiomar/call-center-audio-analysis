$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path '.').Path
$cache = (Resolve-Path "$env:USERPROFILE/.cache/huggingface/hub").Path
$manifest = '.local/multilingual-asr-20261029/manifest.json'
$manifestHash = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()
$evidence = Join-Path $workspace 'docs/benchmarks/evidence/multilingual-20261029'
$jobs = @(
    @('tiny','whisper','/models/models--Systran--faster-whisper-tiny/snapshots/d90ca5fe260221311c53c58e660288d3deb8d356','project28-upgrade-whisper:local'),
    @('small','whisper','/models/models--Systran--faster-whisper-small/snapshots/536b0662742c02347bc0e980a01041f333bce120','project28-upgrade-whisper:local'),
    @('turbo','whisper','/workspace/.local/model-upgrade-20261029/turbo','project28-upgrade-whisper:local'),
    @('qwen06','qwen','/workspace/.local/step13-qwen3-asr-0.6b','project28-step13-qwen:headers'),
    @('qwen17','qwen','/workspace/.local/model-upgrade-20261029/qwen17','project28-step13-qwen:headers'),
    @('parakeet','parakeet','/workspace/.local/model-upgrade-20261029/parakeet','project28-upgrade-benchmark:local')
)
foreach ($job in $jobs) {
    if (Test-Path -LiteralPath (Join-Path $evidence "$($job[0]).json")) { throw "Output already exists: $($job[0])" }
}
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
        $started = (Get-Date).ToUniversalTime().ToString('o')
        $output = "docs/benchmarks/evidence/multilingual-20261029/$($job[0]).json"
        $arguments = @('run','--rm','--gpus','all','--network','none','--entrypoint','python',
            '-v',"${workspace}:/workspace",'-v',"${cache}:/models:ro",'-w','/workspace',
            $job[3],'-u','scripts/benchmark_upgrade_asr.py','--backend',$job[1],
            '--model',$job[2],'--device','cuda','--repetitions','1','--output',$output,
            '--manifest',$manifest,'--manifest-sha256',$manifestHash)
        if ($job[0] -eq 'parakeet') { $arguments += @('--languages','fr') }
        & docker @arguments *> (Join-Path $workspace ".local/multilingual-asr-20261029/$($job[0]).log")
        $code = $LASTEXITCODE
        $receipts += @{model=$job[0]; arguments=$arguments; exit_code=$code; started_utc=$started;
            finished_utc=(Get-Date).ToUniversalTime().ToString('o')}
        $receipts | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $evidence 'execution.json')
        Write-Output "$($job[0]) exit $code"
    }
}
finally {
    if ($stopped) {
        & docker start ollama
        Write-Output 'Ollama restarted'
    }
}
if (@($receipts | Where-Object {$_.exit_code -ne 0}).Count -gt 0) { exit 1 }
