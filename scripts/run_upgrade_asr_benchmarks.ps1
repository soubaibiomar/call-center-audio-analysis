param([int]$WaitForProcess = 0, [ValidateSet('all','whisper')] [string]$Group = 'all')
$ErrorActionPreference = 'Stop'
if ($WaitForProcess -gt 0) {
    Wait-Process -Id $WaitForProcess -ErrorAction SilentlyContinue
}
$workspace = (Resolve-Path '.').Path
$cache = (Resolve-Path "$env:USERPROFILE/.cache/huggingface/hub").Path
$evidence = Join-Path $workspace 'docs/benchmarks/evidence/upgrade-20261029'
$privateLogs = Join-Path $workspace '.local/model-upgrade-20261029'
$jobs = @(
    @('tiny-cuda','whisper','/models/models--Systran--faster-whisper-tiny/snapshots/d90ca5fe260221311c53c58e660288d3deb8d356','project28-upgrade-whisper:local','cuda'),
    @('small-cuda','whisper','/models/models--Systran--faster-whisper-small/snapshots/536b0662742c02347bc0e980a01041f333bce120','project28-upgrade-whisper:local','cuda'),
    @('turbo-cuda','whisper','/workspace/.local/model-upgrade-20261029/turbo','project28-upgrade-whisper:local','cuda'),
    @('qwen06-cuda','qwen','/workspace/.local/step13-qwen3-asr-0.6b','project28-step13-qwen:headers','cuda'),
    @('qwen17-cuda','qwen','/workspace/.local/model-upgrade-20261029/qwen17','project28-step13-qwen:headers','cuda'),
    @('parakeet-cuda','parakeet','/workspace/.local/model-upgrade-20261029/parakeet','project28-upgrade-benchmark:local','cuda'),
    @('tiny-cpu-container','whisper','/models/models--Systran--faster-whisper-tiny/snapshots/d90ca5fe260221311c53c58e660288d3deb8d356','project28-upgrade-benchmark:local','cpu')
)
$receipts = @()
$receiptPath = Join-Path $evidence 'asr-execution.json'
if (Test-Path -LiteralPath $receiptPath) {
    $receipts = @(Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json)
}
foreach ($job in $jobs) {
    if ($Group -eq 'whisper' -and ($job[1] -ne 'whisper' -or $job[4] -ne 'cuda')) { continue }
    $output = "docs/benchmarks/evidence/upgrade-20261029/asr-$($job[0]).json"
    if (Test-Path -LiteralPath $output) { throw "Output exists: $output" }
    $started = (Get-Date).ToUniversalTime().ToString('o')
    $arguments = @('run','--rm','--gpus','all','--network','none','--entrypoint','python',
        '-v',"${workspace}:/workspace",'-v',"${cache}:/models:ro",'-w','/workspace',
        $job[3],'-u','scripts/benchmark_upgrade_asr.py','--backend',$job[1],
        '--model',$job[2],'--device',$job[4],'--output',$output)
    & docker @arguments *> (Join-Path $privateLogs "asr-$($job[0]).log")
    $status = $LASTEXITCODE
    $receipts += @{name=$job[0]; arguments=$arguments; started_utc=$started;
        finished_utc=(Get-Date).ToUniversalTime().ToString('o'); exit_code=$status}
    $receipts | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $receiptPath
    Write-Output "$($job[0]) exit $status"
}
